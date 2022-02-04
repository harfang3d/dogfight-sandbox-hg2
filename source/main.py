# Copyright (C) 2018-2021 Eric Kernin, NWNC HARFANG.

import harfang as hg
from master import Main
import data_converter as dc
import states
from Particles import *
import network_server as netws
import time
import sys
from os import path, getcwd

# --------------- Inline arguments handler

main_name = sys.argv.pop(0)

for i in range(len(sys.argv)):
    cmd = sys.argv[i]
    if cmd == "network_port":
        try:
            nwport = int(sys.argv[i+1])
            netws.dogfight_network_port = nwport
            print("Network port:" + str(nwport))
        except:
            print("ERROR !!! Bad port format - network port must be a valid number !!!")
        i += 1
    elif cmd == "vr_mode":
        Main.flag_vr = True


# --------------- Compile assets:
print("Compiling assets...")
if sys.platform == "linux" or sys.platform == "linux2":
    assetc_cmd = [path.join(getcwd(), "../", "bin", "assetc", "assetc"), "assets", "-quiet", "-progress"]
    dc.run_command(assetc_cmd)
else:
    dc.run_command("../bin/assetc/assetc assets -quiet -progress")

# --------------- Init system

hg.InputInit()
hg.WindowSystemInit()

hg.SetLogDetailed(False)

res_x, res_y = int(Main.resolution.x), int(Main.resolution.y)

hg.AddAssetsFolder(Main.assets_compiled)

# ------------------- Setup output window

def get_monitor_mode(width, height):
    monitors = hg.GetMonitors()
    for i in range(monitors.size()):
        monitor = monitors.at(i)
        f, monitorModes = hg.GetMonitorModes(monitor)
        if f:
            for j in range(monitorModes.size()):
                mode = monitorModes.at(j)
                if mode.rect.ex == width and mode.rect.ey == height:
                    print("get_monitor_mode() : Width %d Height %d" % (mode.rect.ex, mode.rect.ey))
                    return monitor, j
    return None, 0


Main.win = None
if Main.fullscreen:
    monitor, mode_id = get_monitor_mode(res_x, res_y)
    if monitor is not None:
        Main.win = hg.NewFullscreenWindow(monitor, mode_id)

if Main.win is None:
    Main.win = hg.NewWindow(res_x, res_y)

hg.RenderInit(Main.win)
hg.RenderReset(res_x, res_y, hg.RF_None) # hg.RF_VSync | hg.RF_MSAA4X | hg.RF_MaxAnisotropy)


# -------------------- OpenVR initialization

if Main.flag_vr:
    if not Main.setup_vr():
        sys.exit()

# ------------------- Imgui for UI

imgui_prg = hg.LoadProgramFromAssets('core/shader/imgui')
imgui_img_prg = hg.LoadProgramFromAssets('core/shader/imgui_image')
hg.ImGuiInit(10, imgui_prg, imgui_img_prg)


# --------------------- Setup dogfight sim
hg.AudioInit()
Main.init_game()

node = Main.scene.GetNode("platform.S400")
nm = node.GetName()

# rendering pipeline
Main.pipeline = hg.CreateForwardPipeline()
hg.ResetClock()

# ------------------- Setup state:
Main.current_state = states.init_menu_phase()

# ------------------- Main loop:

while not Main.flag_exit:

    Main.update_inputs()
    if not Main.flag_client_update_mode:
        Main.update()
    else:
        time.sleep(1 / 60)
    Main.update_window()

# ----------------- Exit:

if Main.flag_network_mode:
    netws.stop_server()

hg.StopAllSources()
hg.AudioShutdown()

hg.RenderShutdown()
hg.DestroyWindow(Main.win)
