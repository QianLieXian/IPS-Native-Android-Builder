import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from fix_converter import fix_windows

UNITY = "6000.3.25f1"
ABI = "armeabi-v7a"
PACKAGE = "io.github.qianliexian.ips.nativeapp"
DATA = Path("assets") / "bin" / "Data"
ORIGINAL_DLL_HASH = "3f8c9df6d9a6702895b23fa9fcb2e327e2f8befe7b139eb8a911de8b6c7095a8"
PMUNITY_REV = "7887f93db4cb383f9c0f0aef6749d5ecc52819a8"
UNITY_INSTALLER = f"UnitySetup-Android-Support-for-Editor-{UNITY}.exe"
JDK_ZIP = "microsoft-jdk-17.0.21.1-windows-x64.zip"

DOWNLOADS = {
    "pip-26.3-py3-none-any.whl": (
        "https://files.pythonhosted.org/packages/07/25/ee8c38ae72d66b844ce8eb9711ba905dba21ca1a8a0c960057c41cd23337/pip-26.3-py3-none-any.whl",
        "f3b60b20ffaadd4415ed7957212a38ac63fa4c5fa375bd0f4a797777940fad13"),
    "portmaster-unity.zip": (
        f"https://codeload.github.com/wild1walker/portmaster-unity/zip/{PMUNITY_REV}",
        "77d3513f00b6e52db21b4dcdf984ad1e7bf9ce38ed30087e9aa4a78d9a8c26bd"),
    UNITY_INSTALLER: (
        f"https://download.unity3d.com/download_unity/e1dba0a9aba4/TargetSupportInstaller/{UNITY_INSTALLER}",
        "afe9637c7bd9bf58d3f58acc8acfda713be65a250cb1c5ad8543170defa31b69"),
    JDK_ZIP: (
        f"https://aka.ms/download-jdk/{JDK_ZIP}",
        "a07e270f86aec056d9c2acf981eb64a38e30814dacfadbc5f80f31c55d5a4427"),
    "build-tools_r35_windows.zip": (
        "https://dl.google.com/android/repository/build-tools_r35_windows.zip",
        "5753c679a1b90bcf6fbc9945a2ce39dfb9e74f1df0831a1e1866ae5b594326f0"),
    "platform-35-ext15_r01.zip": (
        "https://dl.google.com/android/repository/platform-35-ext15_r01.zip",
        "a93712aedd4f851d9cf1f7281f7c4fe5581ce03a9df37ffc8c53a487eadf311f"),
    "mono.cecil.0.11.6.nupkg": (
        "https://api.nuget.org/v3-flatcontainer/mono.cecil/0.11.6/mono.cecil.0.11.6.nupkg",
        "d2a23832aaa948ba9a01acc42b5726e34c5f995958f1b30d45c0e7c70b3a72d5"),
}


def run(*args, cwd=None):
    subprocess.run([str(arg) for arg in args], cwd=cwd, check=True)


def sha256(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def download(cache, filename):
    path = cache / "downloads" / filename
    url, checksum = DOWNLOADS[filename]
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.is_file():
        print(f"Downloading {filename}", flush=True)
        partial = path.with_suffix(path.suffix + ".part")
        run("curl.exe", "--fail", "--location", "--retry", "2", "--output", partial, url)
        if sha256(partial) != checksum:
            partial.unlink()
            raise ValueError(f"SHA-256 mismatch: {filename}")
        partial.replace(path)
    elif sha256(path) != checksum:
        raise ValueError(f"SHA-256 mismatch. Remove the cached archive and retry: {path}")
    return path


def unpack(cache, filename, target, sentinel):
    directory = cache / target
    marker = directory / ".ready"
    if not marker.is_file():
        archive = download(cache, filename)
        with zipfile.ZipFile(archive) as source:
            source.extractall(directory)
        if not (directory / sentinel).is_file():
            raise ValueError(f"Expected {sentinel} in {filename}")
        marker.touch()
    return directory


def provision(cache):
    py_site = Path(sys.executable).parent / "Lib" / "site-packages"
    marker = cache / "python-packages.ready"
    source = unpack(cache, "portmaster-unity.zip", "portmaster-unity", f"portmaster-unity-{PMUNITY_REV}/convert/requirements.txt")
    converter = source / f"portmaster-unity-{PMUNITY_REV}" / "convert"
    if not marker.is_file():
        wheel = download(cache, "pip-26.3-py3-none-any.whl")
        with zipfile.ZipFile(wheel) as package:
            package.extractall(py_site)
        run(sys.executable, "-m", "pip", "install", "setuptools==84.2.1", "wheel==0.48.0")
        run(sys.executable, "-m", "pip", "install", "--no-build-isolation", "-r", converter / "requirements.txt")
        marker.touch()

    jdk = unpack(cache, JDK_ZIP, "jdk", "jdk-17.0.21.1+2/bin/javac.exe") / "jdk-17.0.21.1+2" / "bin"
    tools = unpack(cache, "build-tools_r35_windows.zip", "build-tools", "android-15/aapt2.exe") / "android-15"
    android_jar = unpack(cache, "platform-35-ext15_r01.zip", "sdk", "android-35-ext15/android.jar") / "android-35-ext15" / "android.jar"
    cecil = unpack(cache, "mono.cecil.0.11.6.nupkg", "cecil", "lib/net40/Mono.Cecil.dll") / "lib" / "net40" / "Mono.Cecil.dll"
    return converter, jdk, tools, android_jar, cecil


def pmunity(converter, *args):
    run(sys.executable, "-u", "-c",
        "import os,sys; sys.path.insert(0,os.getcwd()); from pmunity.__main__ import main; main()",
        *args, cwd=converter)


def get_player(cache, converter):
    player = cache / f"unity-android-{UNITY}"
    generated = player / "reference"
    marker = player / ".ready"
    if not marker.is_file():
        installer = download(cache, UNITY_INSTALLER)
        pmunity(converter, "player", "fetch", UNITY, player, "--installer", installer, "--backend", "mono", "--abi", ABI)
        run(sys.executable, "-c",
            "import os,sys; sys.path.insert(0,os.getcwd()); from pmunity.nsis import main; main()",
            "extract", installer, generated,
            "*/Variations/mono/Release/Classes/classes.jar",
            "*/Apk/res/values/unityLibrary/strings.xml",
            "*/Source/com/unity3d/player/UnityPlayerActivity.java", cwd=converter)
        marker.touch()
        installer.unlink()
    return player, generated / "_OUTDIR"


def link_or_copy(src, dst):
    try:
        os.link(src, dst)
    except OSError:
        shutil.copyfile(src, dst)


def overlay_sources(game, converted):
    for item in game.rglob("*"):
        relative = item.relative_to(game)
        if not item.is_file() or relative.parts[0] == "Plugins":
            continue
        if relative.parts[0] == "MonoBleedingEdge" and relative.parts[1:2] != ("etc",):
            continue
        destination = converted / relative
        if not destination.exists():
            destination.parent.mkdir(parents=True, exist_ok=True)
            link_or_copy(item, destination)


def update_assembly_list(path, managed, include_controls=False):
    metadata = json.loads(path.read_text(encoding="utf-8"))
    entries = list(zip(metadata["names"], metadata["types"], strict=True))
    if not (managed / "MCPForUnity.Runtime.dll").is_file():
        entries = [entry for entry in entries if entry[0] != "MCPForUnity.Runtime.dll"]
    if include_controls:
        entries.append(("IPS.NativeControls.dll", 16))
    metadata["names"], metadata["types"] = zip(*entries, strict=True)
    update = path.with_suffix(".json.tmp")
    update.write_text(json.dumps(metadata, separators=(",", ":")), encoding="utf-8")
    update.replace(path)


def build_managed(game, data, cecil, work):
    managed = data / "Managed"
    original = game / "Managed" / "Assembly-CSharp.dll"
    csc = Path(os.environ["WINDIR"]) / "Microsoft.NET" / "Framework64" / "v4.0.30319" / "csc.exe"
    controls = managed / "IPS.NativeControls.dll"
    references = ("mscorlib.dll", "netstandard.dll", "UnityEngine.CoreModule.dll", "UnityEngine.AndroidJNIModule.dll")
    run(csc, "/nologo", "/noconfig", "/nostdlib+", "/target:library", "/optimize+",
        *(f"/reference:{managed / ref}" for ref in references), f"/reference:{original}",
        f"/out:{controls}", ROOT / "managed" / "NativeControls.cs")
    patched = work / "Assembly-CSharp.dll"
    run("powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
        ROOT / "managed" / "Patch-Game.ps1", original, patched, cecil, controls)
    patched.replace(managed / original.name)
    update_assembly_list(data / "ScriptingAssemblies.json", managed, include_controls=True)


def build_shell(reference, jdk, tools, android_jar, work):
    resources, classes, dex = (work / part for part in ("res", "classes", "dex"))
    (resources / "values").mkdir(parents=True)
    classes.mkdir()
    dex.mkdir()
    shutil.copyfile(ROOT / "android" / "app.xml", resources / "values" / "app.xml")
    shutil.copyfile(reference / "Apk" / "res" / "values" / "unityLibrary" / "strings.xml",
                    resources / "values" / "game-view.xml")
    compiled_resources, shell_apk = work / "resources.zip", work / "shell.apk"
    aapt = tools / "aapt2.exe"
    run(aapt, "compile", "--dir", resources, "-o", compiled_resources)
    run(aapt, "link", "-I", android_jar, "--manifest", ROOT / "android" / "AndroidManifest.xml",
        "--min-sdk-version", "24", "--target-sdk-version", "35", "-o", shell_apk, compiled_resources)
    unity_jar = reference / "Variations" / "mono" / "Release" / "Classes" / "classes.jar"
    activity = reference / "Source" / "com" / "unity3d" / "player" / "UnityPlayerActivity.java"
    run(jdk / "javac.exe", "--release", "8", "-encoding", "UTF-8",
        "-cp", f"{android_jar}{os.pathsep}{unity_jar}", "-d", classes, activity,
        ROOT / "android" / "MainActivity.java")
    activity_jar = work / "activities.jar"
    run(jdk / "jar.exe", "cf", activity_jar, "-C", classes, ".")
    run(jdk / "java.exe", "-cp", tools / "lib" / "d8.jar", "com.android.tools.r8.D8",
        "--release", "--min-api", "24", "--lib", android_jar, "--output", dex, activity_jar, unity_jar)
    return shell_apk, dex / "classes.dex"


def assemble(shell, dex, data, player, output):
    runtime = player / "Variations" / "mono" / "Release"
    with zipfile.ZipFile(shell) as base, zipfile.ZipFile(output, "w", allowZip64=False) as apk:
        for item in base.infolist():
            apk.writestr(item, base.read(item))
        apk.write(dex, "classes.dex", compress_type=zipfile.ZIP_DEFLATED)
        for folder in ("Libs", "MonoLibs"):
            for lib in sorted((runtime / folder / ABI).glob("*.so")):
                apk.write(lib, f"lib/{ABI}/{lib.name}")
        for item in sorted((data / "assets").rglob("*")):
            if item.is_file():
                apk.write(item, item.relative_to(data).as_posix())


def sign_and_verify(jdk, tools, cache, work, unsigned, final):
    key = cache / "local-signing.jks"
    if not key.is_file():
        run(jdk / "keytool.exe", "-genkeypair", "-noprompt", "-keystore", key,
            "-storepass", "android", "-keypass", "android", "-alias", "androiddebugkey",
            "-dname", "CN=IPS Local APK", "-keyalg", "RSA", "-keysize", "2048", "-validity", 10000)
    aligned, signed = work / "aligned.apk", work / "signed.apk"
    zipalign = tools / "zipalign.exe"
    run(zipalign, "-f", "-P", "16", "4", unsigned, aligned)
    signer = (jdk / "java.exe", "-jar", tools / "lib" / "apksigner.jar")
    run(*signer, "sign", "--ks", key, "--ks-key-alias", "androiddebugkey", "--ks-pass", "pass:android",
        "--key-pass", "pass:android", "--v4-signing-enabled", "false", "--out", signed, aligned)
    run(*signer, "verify", "--verbose", signed)
    run(zipalign, "-c", "-P", "16", "4", signed)
    with zipfile.ZipFile(signed) as apk:
        if apk.testzip() is not None:
            raise ValueError("The built APK failed its ZIP CRC check.")
        with apk.open(f"lib/{ABI}/libunity.so") as engine:
            header = engine.read(20)
        if header[:6] != b"\x7fELF\x01\x01" or header[18:20] != b"\x28\x00":
            raise ValueError("The APK is missing the Unity ARMv7 engine.")
    shutil.copyfile(signed, final.with_suffix(".apk.tmp"))
    final.with_suffix(".apk.tmp").replace(final)


def main(game, cache, output):
    source_assembly = game / "Managed" / "Assembly-CSharp.dll"
    if not source_assembly.is_file() or sha256(source_assembly) != ORIGINAL_DLL_HASH:
        raise ValueError("This release supports the tested Linux 2.5.0 Supporter build. Check your extracted game folder.")
    cache.mkdir(parents=True, exist_ok=True)
    output.mkdir(parents=True, exist_ok=True)
    converter, jdk, tools, android_jar, cecil = provision(cache)
    player, reference = get_player(cache, converter)
    with tempfile.TemporaryDirectory(prefix="ips-build-", dir=cache) as temp:
        work = Path(temp)
        local_converter = work / "convert"
        shutil.copytree(converter, local_converter, ignore=shutil.ignore_patterns("__pycache__"))
        fix_windows(local_converter)
        converted = work / "converted"
        pmunity(local_converter, "convert", game, converted, "--config", ROOT / "conversion.json")
        overlay_sources(game, converted)
        update_assembly_list(converted / "ScriptingAssemblies.json", converted / "Managed")
        pmunity(local_converter, "android-data", "--src", converted, "--pkg", player,
                "--out", work / "data", "--name", "IPS", "--no-inline-textures",
                "--graphics-apis", "21", "--no-video-shader", "--package", PACKAGE)
        payload = work / "data" / "IPS"
        build_managed(game, payload / DATA, cecil, work)
        shell, dex = build_shell(reference, jdk, tools, android_jar, work)
        unsigned = work / "unsigned.apk"
        assemble(shell, dex, payload, player, unsigned)
        final = output / "Isekai-Parlor-Simulator-2.5.0-Native-Android.apk"
        sign_and_verify(jdk, tools, cache, work, unsigned, final)
    print(f"APK: {final}")
    print(f"SHA-256: {sha256(final)}")


if __name__ == "__main__":
    try:
        main(*(Path(value).resolve() for value in sys.argv[1:]))
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print(f"Build failed: {error}", file=sys.stderr)
        sys.exit(1)
