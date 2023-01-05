# Copyright (C) 2018-2021 Eric Kernin, Thomas Simonnet, NWNC HARFANG.

# Reading advanced gamepad state

import harfang as hg


hg.InputInit()
hg.WindowSystemInit()

res_x, res_y = 600, 800
win = hg.NewWindow(res_x, res_y)
hg.RenderInit(win, hg.RT_OpenGL)
hg.RenderReset(res_x, res_y, hg.RF_MSAA4X | hg.RF_MaxAnisotropy)

hg.AddAssetsFolder("assets_compiled")

imgui_prg = hg.LoadProgramFromAssets("core/shader/imgui")
imgui_img_prg = hg.LoadProgramFromAssets("core/shader/imgui_image")

hg.ImGuiInit(10, imgui_prg, imgui_img_prg)

joysticks = hg.GetJoystickNames()
for joystick_name in joysticks:
	joystick = hg.Joystick(joystick_name)
	dev_name = joystick.GetDeviceName()
	print(joystick_name + " - " + dev_name)
vr_controller_names = hg.GetVRControllerNames()
for vrc_name in vr_controller_names:
	print(vrc_name)

while not hg.ReadKeyboard().Key(hg.K_Escape):
	hg.ImGuiBeginFrame(res_x, res_y, hg.TickClock(), hg.ReadMouse(), hg.ReadKeyboard())


	joysticks = hg.GetJoystickNames()

	for joystick_name in joysticks:
		generic_controller = hg.Joystick(joystick_name)
		generic_controller.Update()
		if generic_controller.IsConnected():
			dev_name = generic_controller.GetDeviceName()
			if hg.ImGuiCollapsingHeader(joystick_name + " - " + dev_name):
				hg.ImGuiIndent()
				for j in range(generic_controller.ButtonsCount()):
					hg.ImGuiText(f"button {j}: {generic_controller.Down(j)}")
				for j in range(generic_controller.AxesCount()):
					hg.ImGuiText(f"axe {j}: {generic_controller.Axes(j)}")
				hg.ImGuiUnindent()
		#else:
		#	hg.ImGuiText(f"Joystick not connected - " + joystick_name)
	
	"""
	gamespads = hg.GetGamepadNames()
	
	for gp_name in gamespads:
		gamepad_controller = hg.Gamepad(gp_name)
		gamepad_controller.Update()
		if gamepad_controller.IsConnected():
			if hg.ImGuiCollapsingHeader("gamepad: " + gp_name):
				hg.ImGuiIndent()
				for j in range(16):
					hg.ImGuiText(f"button {j}: {gamepad_controller.Down(j)}")
				for j in range(10):
					hg.ImGuiText(f"axe {j}: {gamepad_controller.Axes(j)}")
				hg.ImGuiUnindent()
		#else:
		#	hg.ImGuiText("Gamepad Controller not connected - " + gp_name)
	"""

	hg.SetView2D(0, 0, 0, res_x, res_y, -1, 1, hg.CF_Color | hg.CF_Depth, hg.Color.Black, 1, 0)
	hg.ImGuiEndFrame(0)
	hg.Frame()
	hg.UpdateWindow(win)

hg.RenderShutdown()
hg.DestroyWindow(win)
