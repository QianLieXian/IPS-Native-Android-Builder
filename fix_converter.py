def replace_once(source, old, new):
    if source.count(old) != 1:
        raise ValueError(f"Unexpected converter source around {old.splitlines()[0]!r}")
    return source.replace(old, new, 1)


def fix_windows(converter):
    job_path = converter / "pmunity" / "job.py"
    job = job_path.read_text(encoding="utf-8")
    job = replace_once(job, "import json, os, sys, time", "import json, os, shutil, sys, time")
    job = replace_once(job, "st = os.statvfs(self.out)\n        free = st.f_bavail * st.f_frsize",
                       "free = shutil.disk_usage(self.out).free")
    job_path.write_text(job, encoding="utf-8")

    path = converter / "pmunity" / "android_data.py"
    source = path.read_text(encoding="utf-8")
    source = replace_once(source, "_libc = ctypes.CDLL(None, use_errno=True)",
                          "_libc = ctypes.CDLL(None, use_errno=True) if os.name != 'nt' else None")
    source = replace_once(source, """        elif n == 'PlayerSettings':
            # (6000.x, 2023.2.20f1:""", """        elif n == 'PlayerSettings' and str(args.unity) == '6000.3.25f1':
            # The bundled type tree diverges after the minimum GLES version on this build.
            # Preserve the rest of PlayerSettings byte-for-byte.
            raw = bytearray(o.get_raw_data())
            if (len(raw) != 900
                    or raw[0x38:0x3c] != struct.pack('<i', 23)
                    or raw[0x3c:0x53] != b'Isekai Parlor Simulator'
                    or raw[0x120] not in (0, 1)
                    or raw[0x121] != 0
                    or raw[0x134:0x138] != bytes(4)):
                raise ValueError('Unexpected Linux PlayerSettings layout')
            raw[0x121] = raw[0x120]
            o.set_raw_data(bytes(raw))
            notes.append('PlayerSettings: enabled the mobile rendering thread')
        elif n == 'PlayerSettings':
            # (6000.x, 2023.2.20f1:""")
    source = replace_once(source, """                for o in sf.objects.values():
                    typetrees.read(o)""", """                for o in sf.objects.values():
                    if o.type.name != 'PlayerSettings' or str(args.unity) != '6000.3.25f1':
                        typetrees.read(o)""")
    path.write_text(source, encoding="utf-8")
