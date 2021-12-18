# Copyright (C) 2018-2021 Eric Kernin, Thomas Simonnet, NWNC HARFANG.

# Reading advanced gamepad state

import harfang as hg

hg.InputInit()
hg.WindowSystemInit()

res_x, res_y = 600, 800
win = hg.RenderInit('Harfang - Read Gamepad', res_x, res_y, hg.RF_VSync)

hg.AddAssetsFolder('assets_compiled')

imgui_prg = hg.LoadProgramFromAssets('core/shader/imgui')
imgui_img_prg = hg.LoadProgramFromAssets('core/shader/imgui_image')

hg.ImGuiInit(10, imgui_prg, imgui_img_prg)


while not hg.ReadKeyboard().Key(hg.K_Escape):
	hg.ImGuiBeginFrame(res_x, res_y, hg.TickClock(), hg.ReadMouse(), hg.ReadKeyboard())

	for i in range(16):
		generic_controller = hg.Joystick(f"generic_controller_slot_{i}")
		generic_controller.Update()
		if generic_controller.IsConnected():
			if hg.ImGuiCollapsingHeader(f"generic_controller_slot_{i}"):
				hg.ImGuiIndent()
				for j in range(generic_controller.ButtonsCount()):
					hg.ImGuiText(f"button {j}: {generic_controller.Down(j)}")
				for j in range(generic_controller.AxesCount()):
					hg.ImGuiText(f"axe {j}: {generic_controller.Axes(j)}")
				hg.ImGuiUnindent()
		else:
			hg.ImGuiText(f"Generic Controller: {i} not connected")


	gamepad_controller = hg.Gamepad()
	gamepad_controller.Update()
	if gamepad_controller.IsConnected():
		if hg.ImGuiCollapsingHeader("gamepad"):
			hg.ImGuiIndent()
			for j in range(10):
				hg.ImGuiText(f"button {j}: {gamepad_controller.Down(j)}")
			for j in range(10):
				hg.ImGuiText(f"axe {j}: {gamepad_controller.Axes(j)}")
			hg.ImGuiUnindent()
	else:
		hg.ImGuiText("Gamepad Controller not connected")



	hg.SetView2D(0, res_x, res_y, -1, 1, 1, 100, hg.CF_Color | hg.CF_Depth, hg.Color.Black, 1, 0)
	hg.ImGuiEndFrame(0)
	hg.Frame()
	hg.UpdateWindow(win)

hg.DestroyWindow(win)
