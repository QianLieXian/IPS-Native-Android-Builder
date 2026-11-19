param([string]$InputAssembly,[string]$OutputAssembly,[string]$Cecil,[string]$ControlsAssembly)
$ErrorActionPreference='Stop'
Add-Type -Path $Cecil
$assembly=[Mono.Cecil.AssemblyDefinition]::ReadAssembly($InputAssembly)
try {
    $module=$assembly.MainModule
    $menu=$module.GetType('IPS.Engine.Player.UI.UIMainMenu')
    $controller=$module.GetType('IPS.Engine.Player.ApplicationController')
    $progress=$module.GetType('IPS.Engine.Player.PlayerProgress')
    $handler=$menu.Methods | Where-Object Name -eq 'OnPlayerProgressLoaded'
    $getter=$controller.Methods | Where-Object Name -eq 'get_PlayerProgress'
    $ctor=$progress.Methods | Where-Object Name -eq '.ctor'
    if ($handler.Parameters.Count -ne 2 -or !$getter.IsStatic -or $ctor.Parameters.Count -ne 0) {
        throw 'Unexpected signatures in the player-progress handler.'
    }
    $block=$handler.Body.GetILProcessor()
    $first=$handler.Body.Instructions[0]
    $assign=$block.Create([Mono.Cecil.Cil.OpCodes]::Starg,$handler.Parameters[1])
    $prefix=@(
        $block.Create([Mono.Cecil.Cil.OpCodes]::Ldarg_2)
        $block.Create([Mono.Cecil.Cil.OpCodes]::Brtrue,$first)
        $block.Create([Mono.Cecil.Cil.OpCodes]::Call,$getter)
        $block.Create([Mono.Cecil.Cil.OpCodes]::Dup)
        $block.Create([Mono.Cecil.Cil.OpCodes]::Brtrue,$assign)
        $block.Create([Mono.Cecil.Cil.OpCodes]::Pop)
        $block.Create([Mono.Cecil.Cil.OpCodes]::Newobj,$ctor)
        $assign
    )
    foreach ($instruction in $prefix) {
        $block.InsertBefore($first,$instruction)
    }
    $handler.Body.MaxStackSize=[math]::Max($handler.Body.MaxStackSize,2)
    $helper=[Mono.Cecil.AssemblyDefinition]::ReadAssembly($ControlsAssembly)
    try {
        $tick=$helper.MainModule.GetType('IPS.AndroidPort.NativeControls').Methods | Where-Object Name -eq Tick
        $debug=$module.GetType('IPS.Engine.Player.UI.UIDebug')
        $update=$debug.Methods | Where-Object Name -eq Update
        $world=$debug.Fields | Where-Object Name -eq m_World
        if ($tick.Parameters.Count -ne 1 -or $world.FieldType.FullName -ne $tick.Parameters[0].ParameterType.FullName) {
            throw 'Unexpected signatures in the debug controller.'
        }
        $il=$update.Body.GetILProcessor()
        $start=$update.Body.Instructions[0]
        $il.InsertBefore($start,$il.Create([Mono.Cecil.Cil.OpCodes]::Ldarg_0))
        $il.InsertBefore($start,$il.Create([Mono.Cecil.Cil.OpCodes]::Ldfld,$world))
        $il.InsertBefore($start,$il.Create([Mono.Cecil.Cil.OpCodes]::Call,$module.ImportReference($tick)))
        $assembly.Write($OutputAssembly)
    } finally {
        $helper.Dispose()
    }
} finally {
    $assembly.Dispose()
}