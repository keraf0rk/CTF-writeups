rule BurhanGuild_Memory_Loader {
    strings:
        $elf = { 7f 45 4c 46 02 01 01 }
        $cfg = "CFG3"
        $memfd = "memfd:libpam_bg.so"
    condition:
        2 of them
}
