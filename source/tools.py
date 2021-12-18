# Copyright (C) 2018-2021 Eric Kernin, NWNC HARFANG.

import harfang as hg


def get_hierarchy_strate(parent: dict, nodes: hg.NodeList):  # parent={"node":parent_node,"children":[]}
    for i in range(nodes.size()):
        f = False
        nd = nodes.at(i)
        if parent["node"] is None:
            if nd.GetTransform().GetParent() is None:
                f = True
        elif nd.GetTransform().GetParent().GetUid() == parent["node"].GetUid():
            f = True
        if f:
            child = {"node": nd, "children": []}
            get_hierarchy_strate(child, nodes)
            parent["children"].append(child)


def duplicate_hierarchy_to_NodeList(scene: hg.Scene, parent_node: hg.Node, children: list, dupl: hg.NodeList, suffix):
    for i, nd_dict in enumerate(children):
        nd = nd_dict["node"]
        new_node = duplicate_node_object(scene, nd, nd.GetName() + suffix)
        if parent_node is None:
            pn = "None"
        else:
            pn = parent_node.GetName()
        # print("new node : " + new_node.GetName() + " - Parent: " + pn)
        if parent_node is not None: new_node.GetTransform().SetParent(parent_node)
        dupl.push_back(new_node)
        duplicate_hierarchy_to_NodeList(scene, new_node, nd_dict["children"], dupl, suffix)


def duplicate_node_and_children(scene: hg.Scene, parent_node: hg.Node, nodes: hg.NodeList, suffix):
    hierarchy = {"node": parent_node, "children": []}
    """
    for i in range(nodes.size()):
        nd= nodes.at(i)
        if nd.GetTransform().GetParent() is None:
            pn="None"
        else: pn=nd.GetTransform().GetParent().GetName()
        print("Node list - NAME: "+nodes.at(i).GetName() + " - Parent: "+pn)
    """
    get_hierarchy_strate(hierarchy, nodes)
    # print("Nombre de nodes roots : " + str(len(hierarchy["children"])))
    dupl = hg.NodeList()
    if parent_node is not None:
        new_parent_node = duplicate_node_object(scene, parent_node, parent_node.GetName() + suffix)
        dupl.push_back(new_parent_node)
    else:
        new_parent_node = None
    duplicate_hierarchy_to_NodeList(scene, new_parent_node, hierarchy["children"], dupl, suffix)
    return dupl


def duplicate_node_object(scene: hg.Scene, original_node: hg.Node, name):
    ot = original_node.GetTransform()
    obj = original_node.GetObject()
    if obj is None:
        # print("Original node: "+original_node.GetName() + " NO OBJECT")
        new_node = scene.CreateNode(name)
        tr = scene.CreateTransform(ot.GetPos(), ot.GetRot(), ot.GetScale())
        new_node.SetTransform(tr)
    else:
        # print("Original node: " + original_node.GetName() + " OBJECT OK")
        mdl_ref = obj.GetModelRef()
        n = obj.GetMaterialCount()
        materials = []
        for k in range(n):
            materials.append(obj.GetMaterial(k))
        new_node = hg.CreateObject(scene, hg.TransformationMat4(ot.GetPos(), ot.GetRot(), ot.GetScale()), mdl_ref, materials)
        new_node.SetName(name)
    return new_node


def get_node_in_list(name, ndlist: hg.NodeList):
    for i in range(ndlist.size()):
        # print(ndlist.at(i).GetName())
        if ndlist.at(i).GetName() == name:
            return ndlist.at(i)
    return None


def create_spatialized_sound_state(loop):
    state = hg.SpatializedSourceState(hg.TranslationMat4(hg.Vec3(0, 0, 0)))
    state.volume = 1
    state.repeat = loop
    return state


def create_stereo_sound_state(loop):
    state = hg.StereoSourceState()
    state.volume = 1
    state.repeat = loop
    return state


def play_stereo_sound(stereo_ref, stereo_state):
    stereo_state[0].panning = -1
    stereo_state[1].panning = 1
    return [hg.PlayStereo(stereo_ref[0], stereo_state[0]), hg.PlayStereo(stereo_ref[1], stereo_state[1])]


def set_stereo_volume(stereo_ref, volume):
    hg.SetSourceVolume(stereo_ref[0], volume)
    hg.SetSourceVolume(stereo_ref[1], volume)


def get_pixel_bilinear(picture: hg.Picture, pos: hg.Vec2):
    w = picture.GetWidth()
    h = picture.GetHeight()
    x = (pos.x * w - 0.5) % w
    y = (pos.y * h - 0.5) % h
    xi = int(x)
    yi = int(y)
    xf = x - xi
    yf = y - yi
    xi1 = (xi + 1) % w
    yi1 = (yi + 1) % h
    c1 = picture.GetPixelRGBA(xi, yi)
    c2 = picture.GetPixelRGBA(xi1, yi)
    c3 = picture.GetPixelRGBA(xi, yi1)
    c4 = picture.GetPixelRGBA(xi1, yi1)
    c12 = c1 * (1 - xf) + c2 * xf
    c34 = c3 * (1 - xf) + c4 * xf
    c = c12 * (1 - yf) + c34 * yf
    return c
