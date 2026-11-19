# Isekai Parlor Simulator 原生 Android 打包工具

在 Windows 上把你已有的 **Isekai Parlor Simulator 2.5.0 Supporter Linux 版**打包成可侧载的 APK。手机或平板通过 Unity 6000.3.25f1 的 Android ARMv7 运行库和 Vulkan 原生运行游戏。仓库和 Release ZIP 只提供打包脚本与 Android 适配代码，游戏文件和 Unity 运行库在本机准备。

## 一键打包

1. 在 [Releases](../../releases/latest) 下载并解压打包工具 ZIP。
2. 把已有的 Linux 游戏解压到工具旁边的 `linux` 文件夹。下面的 `Isekai Parlor Simulator_Data` 应与 Linux 启动程序同级。
3. 双击 `Build APK.bat`。第一次打包会下载 Unity Android 模块、构建工具和转换依赖。打包完成后，APK 在 `dist` 文件夹。
4. 把 APK 复制到 Android 设备并安装，或者用 `adb install -r` 安装。进入游戏后自动存档保存在应用自己的目录里。

```text
IPS-Native-Android-Builder/
├─ Build APK.bat
└─ linux/
   ├─ Isekai Parlor Simulator.x86_64
   └─ Isekai Parlor Simulator_Data/
      ├─ globalgamemanagers
      └─ Managed/
         └─ Assembly-CSharp.dll
```

如果游戏放在别处，运行下面的命令即可指定目录。使用本地代理时可以加上 `-Proxy`。

```bat
"Build APK.bat" -Linux "E:\Games\Isekai Parlor Simulator\linux" -Proxy "http://127.0.0.1:7897"
```

## 设备和版本要求

- 打包电脑需要 64 位 Windows 10 或 11，以及约 6 GB 的临时可用空间。首次下载约 1.8 GB。签名和校验完成后，脚本自动删除中间文件。`.build-cache` 保留可复用的依赖和本机签名密钥。
- Android 设备需要 Android 7.0 或更新版本，支持 **armeabi-v7a、Vulkan 1.0 与 ASTC**。即使处理器是 64 位，系统也必须可以运行 32 位应用。
- 输入文件限定为已测试的 2.5.0 Supporter Linux 构建。打包脚本用原始 `Assembly-CSharp.dll` 的 SHA-256 检查版本，并把 Linux 包里的 Vulkan 着色器保留下来。Lite、Gold、Demo 和其他版本需要各自验证。
- 同一份密钥可以覆盖安装并保留存档。重新生成密钥后，Android 会将新 APK 视为签名不同的应用。
- 游戏可以离线运行。Steam 成就同步和联网资讯在这个移植中不可用。

## 触屏和内置作弊

游戏内菜单可直接点按。在经营界面轻点右下角的 **★**，会弹出原版 **F9** 的四项内置调试操作。点击后显示数值变化。

| 操作 | 效果 |
| --- | --- |
| 金币 +100 | 增加当前经营的金币 |
| 金币 −100 | 扣除当前经营的金币 |
| 声望 +10 | 提高当前经营的声望 |
| 声望 −10 | 降低当前经营的声望 |

## 实机验证

联想小新 Pad Pro 12.6（TB-Q706F，Android 12）验证了原生 Vulkan 启动、触屏操作、沙盒开局、读写存档和四项作弊操作。实测金币从 `1000` 到 `1100` 再回到 `1000`，声望从 `0` 到 `10` 再回到 `0`。完整剧情及其他机型仍待验证。

## 依赖和来源

- 使用 Unity 官方 Android Build Support 模块提取同版本运行库。工具通过平台头、Vulkan 渲染配置和原生资源布局让 Android Player 读取用户本机的游戏数据，并把桌面纹理转换为 ASTC。 [Unity 6000.3.25f1](https://unity.com/releases/editor/whats-new/6000.3.25f1)
- 数据转换使用固定提交的 PortMaster Unity。所用源码随打包工具运行时下载。 [PortMaster Unity](https://github.com/wild1walker/portmaster-unity/tree/7887f93db4cb383f9c0f0aef6749d5ecc52819a8)
- F9 操作来自原游戏，弹窗调用原有的金币和声望函数。 [作者说明](https://itch.io/post/7489113)
