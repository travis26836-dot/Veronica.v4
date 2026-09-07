# WSL NAT / Hyper-V switch diagnosis

Status: unresolved host switch-driver initialization fault; VirtioProxy HTTPS works.

## Verified evidence

- WSL NAT creation fails in HNS with 0x8007023E; active networking falls back to VirtioProxy.
- VMSP (System32/drivers/vmswitch.sys) is stopped with Win32 exit 31. Its VMSNPXY dependency is running.
- Explicit elevated start of VMSP on September 6 failed again with exit 31. Fresh switch events report DriverEntry status 0xC0000001, followed by unload.
- Elevated DISM ScanHealth: no component-store corruption; exit 0.
- SFC verification of vmswitch.sys: no integrity violations; exit 0. This was a targeted file check, not a full-system SFC scan.
- Driver signature is valid. Installed network-component inventory showed Microsoft components; no third-party filter conflict was established.
- Windows edition is Core (Home), build 26220.8271. VirtualMachinePlatform is enabled. Absence of the full Hyper-V feature is not by itself evidence of corruption on Home.
- No specific bad registry value was identified. Protected network-class enumeration was denied in the non-elevated diagnostic shell; no registry values were changed.
- Latest WSL HTTPS check returned 200 while the NAT fallback warning persisted.

## Changes / cleanup

Only attempted repair was starting the existing VMSP driver; it failed. No feature toggles, network reset, firewall changes, registry edits, Windows reboot or Pod creation occurred in this repair stage. Both elevated helper processes finished. Their temporary scripts were removed after results were captured. Text transcripts and result JSON files remain as diagnostic evidence. Windows-owned servicing logs were not deleted.

## Next checkpoint

Request owner approval before a full Windows restart, as this interrupts open applications. After restart, check VMSP, WSL networking mode, HNS events and bounded HTTPS requests. A reboot is a recovery test, not a verified fix. If failure persists, investigate protected component registration and a scoped VirtualMachinePlatform repair; do not perform blanket registry cleanup or remove WSL distributions.
