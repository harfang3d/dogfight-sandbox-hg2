#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2017-2020 Thomas Simonnet, Movida Production.
import json
import os

import harfang as hg
from datetime import datetime
import data_converter as dc
import sqlite3
import Machines
import MissileLauncherS400

flag_init = False
conn = None
current_id_user = 1
current_id_rec = 1
current_id_play = 1
user_name = ""
user_firstname = ""
user_info = ""
user_birthdate = ""

adding_user = False
recording = False
playing = False
pausing= False
updating_database = False
progress_cptr = 0
render_head = False
timer = 0
previous_timer = 0
recorded_min_time = 0
recorded_max_time = 0
recorded_fps = 60

items = {}
items_list = []
items_names = []
selected_item_idx = 0
selected_record = 0
records = None
records_events = None
last_value_recorded = {}

task_record_in_database = None

items_words_list = ["world", "int", "float", "machine_state"]

fps_record = 60

state = "disable"
request_state = "disable"

# Create recordable items from dogfight scene
def setup_items(main):
    clear_items()
    machines_types = [Machines.Destroyable_Machine.TYPE_AIRCRAFT, Machines.Destroyable_Machine.TYPE_MISSILE,Machines.Destroyable_Machine.TYPE_MISSILE_LAUNCHER, Machines.Destroyable_Machine.TYPE_SHIP]
    for dm in main.destroyables_list:
        if dm.type in machines_types:
            AddItem(dm, ["machine_state"], dm.name)

#item: hg.Node
#params: "world", "pos", "mat4", "enable", "float", "int", "bool", "str"
#container: if not None, contain the value to record
def AddItem(item, params=[], name=None, container=None):
    global items, items_list, items_names
    if isinstance(item, Machines.Destroyable_Machine):
        item.add_listener(event_call_back)
        if name is None:
            name = item.name
        item.name = dc.conform_string(name) # !!! This could change the machine name in the scene !!! Need valid machine name to keep right links references (targets, missiles parents....)

    name = dc.conform_string(name)
    #print("VCR - add item " + name)
    items[name] = {"i": item, "params": params, "container": container, "recording": True}

    items_list.append(items[name])
    items_names.append(name)
    return items[name]

def event_call_back(event_name:str, params:list):
    global records_events
    if recording:
        records_events.append([params["timestamp"], event_name + ":" + str(params["value"]) + ":" + dc.serialize_vec3(params["position"])])

def clear_items():
    global items, items_list, selected_item_idx, items_names, records_events
    selected_item_idx = 0
    items = {}
    items_list = []
    items_names = []
    records_events = []
    
def is_init():
    return flag_init

def init():
    global conn, selected_record, flag_init

    # check everything is set
    if conn is None:
        conn = sqlite3.connect('database.db')
        conn.row_factory = sqlite3.Row
        print("VCR - database connected")

        c = conn.cursor()

        c.execute(f'''SELECT name FROM sqlite_master WHERE type='table' AND name='users';''')
        table_users_exists = c.fetchone()

        c.execute('''CREATE TABLE IF NOT EXISTS users(id_user INTEGER PRIMARY KEY, name TEXT, info TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS records(id_rec INTEGER PRIMARY KEY, name TEXT, min_clock FLOAT, max_clock FLOAT, fps INT,scene_items TEXT, id_user INTEGER REFERENCES users, CONSTRAINT fk_users FOREIGN KEY (id_user) REFERENCES users(id_user) ON DELETE CASCADE)''')
        c.execute('''CREATE TABLE IF NOT EXISTS events(id_rec INTEGER REFERENCES records, c FLOAT, v TEXT)''')
        
        # add default user
        if table_users_exists is None:
            c.execute("INSERT INTO users(name, info) VALUES (\"Default\", ?)", ["HARFANG NWSC User"])
        conn.commit()
        flag_init = True

    selected_record = 0

def create_scene_items_list():
    scene_items = []
    for name, params in items.items():
        item = params["i"]
        if isinstance( item,Machines.Destroyable_Machine): 
            scene_items.append(str(item.type) + ";" + item.model_name + ";" + str(item.nationality) + ";" + name)
    return scene_items

def start_record(name_record):
    global recording, records, records_events, current_id_rec, last_value_recorded
    
    # check if we are already start
    if recording:
        return

    records = None
    records_events = []
    last_value_recorded = {}

    scene_items = ":".join(create_scene_items_list())

    # add record
    c = conn.cursor()
    #c.execute(f'''SELECT id_rec FROM records WHERE id_user={current_id_user} AND name=\"{name_record}\"''')
    #r = c.fetchone()
    #if r is None:
    # insert the new record
    c.execute(f'''INSERT INTO records(id_user, name, fps, scene_items) VALUES ({current_id_user}, \"{name_record}\", {fps_record},\"{scene_items}\")''')
    c.execute(f'''SELECT id_rec FROM records WHERE id_user={current_id_user} AND name=\"{name_record}\"''')
    r = c.fetchone()
            
    if r is not None:
        current_id_rec = r["id_rec"]
    conn.commit()
    print(f"create record: {name_record}, {current_id_rec}")
    
    recording = True

# Coroutine
def record_in_database():
    global updating_database, progress_cptr
    c = conn.cursor()

    # save the current record
    # create db for items
    print("Record items table if necessary")
    i = 0
    n_steps = 2*len(records) + len(records_events)
    for t, record in records.items():
        for name, value in record.items():
            if isinstance(value, str):
                c.execute(f"CREATE TABLE IF NOT EXISTS {name}(id_rec INTEGER, c FLOAT, v TEXT, PRIMARY KEY (id_rec, c), CONSTRAINT fk_record FOREIGN KEY (id_rec) REFERENCES records(id_rec) ON DELETE CASCADE) WITHOUT ROWID;")
            elif isinstance(value, bool):
                c.execute(f"CREATE TABLE IF NOT EXISTS {name}(id_rec INTEGER, c FLOAT, v BOOLEAN, PRIMARY KEY (id_rec, c), CONSTRAINT fk_record FOREIGN KEY (id_rec) REFERENCES records(id_rec) ON DELETE CASCADE) WITHOUT ROWID;")
            elif isinstance(value, int):
                c.execute(f"CREATE TABLE IF NOT EXISTS {name}(id_rec INTEGER, c FLOAT, v INTEGER, PRIMARY KEY (id_rec, c), CONSTRAINT fk_record FOREIGN KEY (id_rec) REFERENCES records(id_rec) ON DELETE CASCADE) WITHOUT ROWID;")
            elif isinstance(value, float):
                c.execute(f"CREATE TABLE IF NOT EXISTS {name}(id_rec INTEGER, c FLOAT, v FLOAT, PRIMARY KEY (id_rec, c), CONSTRAINT fk_record FOREIGN KEY (id_rec) REFERENCES records(id_rec) ON DELETE CASCADE) WITHOUT ROWID;")                
            #c.execute(f"DELETE FROM {name} WHERE id_rec={current_id_rec};")
        progress_cptr = i / n_steps
        i+=1
        if (i % fps_record) == 0:
            yield
    # add value to items
    for t, record in records.items():
        for name, value in record.items():
            c.execute(f"INSERT INTO {name}(id_rec, c, v) VALUES ({current_id_rec}, {t}, \"{value}\");")
        progress_cptr = i / n_steps
        i+=1
        if (i % fps_record) == 0:
            yield
    # record events:
    for evt in records_events:
        c.execute(f"INSERT INTO events(id_rec, c, v) VALUES ({current_id_rec}, {evt[0]}, \"{evt[1]}\");")
        progress_cptr = i / n_steps
        i+=1
        if (i % 10) == 0:
            yield


    c.execute(f"UPDATE records SET max_clock={timer}, min_clock={recorded_min_time}  WHERE id_rec={current_id_rec};")
    #c.execute(f"UPDATE records SET fps={fps_record} WHERE id_rec={current_id_rec};")
    conn.commit()
    yield
    updating_database = False

def stop_record():
    global recording, updating_database, task_record_in_database
    
    # check if we are already stopped
    if not recording:
        return
    recording = False
    task_record_in_database = record_in_database()
    updating_database = True


def update_recording(main, dt):
    global records, timer, previous_timer, last_value_recorded, recorded_min_time
    if records is None:
        records = {}
        previous_timer = main.timer

    timer = main.timer
    if timer - previous_timer > 1.0 / fps_record:
        #print(str(fps_record) + " " + str(timer))
        record = {}
        for name, params in items.items():
            if not params["recording"]:
                continue
            item = params["i"]
            for p in params["params"]:
                v = ""
                n = f"{name}_{p}"
                if p == "machine_state":
                        v = serialize_machine_state(item)
                elif p == "world":
                    v = dc.serialize_mat4(item.GetTransform().GetWorld())
                elif p == "mat4":
                    if params["container"] is not None:
                        v = dc.serialize_mat4(params["container"][item])
                    else:
                        v = dc.serialize_mat4(item)
                elif p == "enable":
                    v = item.IsEnabled()
                elif p == "pos":
                    v = dc.serialize_vec3(hg.GetT(item.GetTransform().GetWorld()))
                elif p in ["int", "float", "bool"]:
                    if params["container"] is not None:
                        v = params["container"][item]
                    else:
                        v = item
                elif p == "str":
                    v = item
                else:
                    v = eval(p["save"])
                    n = f"{name}_{p['i']}"
                if n not in last_value_recorded or (n in last_value_recorded and v != last_value_recorded[n]):
                    last_value_recorded[n] = record[n] = v

        if len(records) == 0:
            recorded_min_time = timer
        records[timer] = record
        previous_timer = timer
    
    #timer += hg.time_to_sec_f(dt)

def create_scene(main, scene_items):
    for scene_item in scene_items:
        item_def = scene_item.split(";")
        item_def[0] = int(item_def[0])
        item_def[2] = int(item_def[2])
        if item_def[0] == Machines.Destroyable_Machine.TYPE_AIRCRAFT:
            main.create_aircraft(item_def[1], item_def[3], item_def[2])
        elif item_def[0] == Machines.Destroyable_Machine.TYPE_MISSILE:
            main.create_missile(item_def[1], item_def[3], item_def[2])
        elif item_def[0] == Machines.Destroyable_Machine.TYPE_MISSILE_LAUNCHER:
            main.create_missile_launcher(item_def[3], item_def[2])
        elif item_def[0] == Machines.Destroyable_Machine.TYPE_SHIP:
            main.create_aircraft_carrier(item_def[3], item_def[2])
    main.init_playground()
    main.user_aircraft = None
    main.setup_views_carousel(True)
    main.set_view_carousel("fps")
    setup_items(main)


def start_play(main):
    global playing, timer
    
    c = conn.cursor()

    # Get record items and create scene
    c.execute(f"SELECT scene_items FROM records where id_rec={current_id_play} and id_user = {current_id_user};")
    r = c.fetchone()
    if r is not None:
        scene_items = r["scene_items"].split(":")
        if len(scene_items) > 0:
            main.destroy_players()
            create_scene(main, scene_items)
            timer = recorded_min_time
            print(str(timer))
            playing = True

    


def stop_play(main):
    global playing, pausing
    playing = False
    pausing = False
    clear_items()
    main.clear_scene()

def pause_play():
    global pausing
    pausing = not pausing


def update_play(main, dt):
    global timer, playing
    
    '''
    def interpolate_mat(name_record):   # TODO not used yet but can be one day
        first_mat = deserialize_matrix(records[first_key][name_record])
        second_mat = deserialize_matrix(records[second_key][name_record])
        t = (timer - float(first_key)) / (float(second_key) - float(first_key))

        pos = first_mat.GetTranslation() + (second_mat.GetTranslation() - first_mat.GetTranslation()) * t
        rot = hg.Quaternion.Slerp(t, hg.Quaternion.FromMatrix3(hg.GetRMatrix(first_mat)),
                                    hg.Quaternion.FromMatrix3(hg.GetRMatrix(second_mat))).ToMatrix3()

        return hg.TransformationMat4(pos, rot)
    '''

    c = conn.cursor()

    for name, params in items.items():
        item = params["i"]
        for p in params["params"]:
            n = f"{name}_{p}"
            #if p not in items_words_list:
            #    n = f"{name}_{p['n']}"
            
            c.execute(f"SELECT v FROM {n} where id_rec={current_id_play} and c <= {timer} ORDER BY c DESC LIMIT 1;")
            r = c.fetchone()
            if r is not None:
                v = r["v"]
                if p == "machine_state":
                    deserialize_machine_state(item, v)
                
                elif p == "world":
                    item.GetTransform().SetWorld(dc.deserialize_mat4(v))
                elif p == "mat4":
                    if params["container"] is not None:
                        params["container"][item] = dc.deserialize_mat4(v)
                    else:
                        item = dc.list_to_mat4(v)
                elif p == "enable":
                    item.Enable() if v else item.Disable()
                elif p == "pos":
                    item.GetTransform().SetWorld(hg.TranslationMat4(dc.deserialize_vec3(v)))
                elif p in ["int", "float", "bool"]:
                    if params["container"] is not None:
                        params["container"][item] = v 
                    else:
                        item = v
                elif p in "str":
                    item = v
                else:
                    eval(p["load"])

    if not pausing:
        timer += hg.time_to_sec_f(dt)

    if timer >= recorded_max_time:
        timer = recorded_max_time
        if not pausing:
            pause_play()


def update_gui_record(main):
    
    global selected_item_idx, recorded_min_time, recorded_max_time, timer, fps_record, current_id_play, selected_record, current_id_user, adding_user, user_name, user_info, recorded_fps, request_state
    
    if hg.ImGuiBegin("Dogfight - Recorder"):
        if adding_user:
            user_name = hg.ImGuiInputText("Name", user_name, 128)[1]
            user_info = hg.ImGuiInputText("Infos", user_info, 128)[1]
            if hg.ImGuiButton("Add"):
                c = conn.cursor()
                c.execute(f'''INSERT INTO users(name, info) VALUES (\"{user_name}\", \"{user_info}\")''')
                conn.commit()
                adding_user = False
            if hg.ImGuiButton("Cancel"):
                adding_user = False

        else:

            if not recording:

                # Users list:
                if hg.ImGuiButton("Add user"):
                    adding_user = True
                    user_name = user_firstname = user_info = user_birthdate = ""
                
                c = conn.cursor()
                c.execute(f'''SELECT name, id_user FROM users''')
                r = c.fetchall()
                users = [(str(user[1]) +" - " + user[0]) for user in r]

                current_id_user -= 1
                f, current_id_user = hg.ImGuiCombo("Users", current_id_user, users)
                if f:
                    selected_record = 0
                current_id_user += 1

                # Items list:
                if len(items_list) > 0:
                    f, d = hg.ImGuiListBox("Items", selected_item_idx, items_names,20)
                    if f:
                        selected_item_idx = d

                # Record:
                if hg.ImGuiButton("Start recording"):
                    name_record = datetime.now().strftime("%m/%d/%Y_%H:%M:%S")
                    start_record(dc.conform_string(name_record))
                
                fps_record = int(hg.ImGuiSliderFloat("Recording FPS", fps_record, 1, 128)[1])

                # Records list:
                c.execute(f'''SELECT name FROM records WHERE id_user={current_id_user}''')
                r = c.fetchall()
                r = [x for xs in r for x in xs]
                selected_record = hg.ImGuiCombo("Records", selected_record, ["None"]+r)[1]

                if selected_record != 0:
                    # get current id record
                    c.execute(f'''SELECT id_rec FROM records WHERE id_user={current_id_user} AND name=\"{r[selected_record-1]}\"''')
                    r = c.fetchone()
                    if r is not None:
                        current_id_play = r["id_rec"]
                        
                    c.execute(f'''SELECT max_clock, min_clock, fps FROM records WHERE id_rec={current_id_play}''')
                    recorded_max_time = 0
                    recorded_min_time = 0
                    recorded_fps = 60
                    r = c.fetchone()
                    if r is not None:
                        recorded_min_time = r["min_clock"]
                        recorded_max_time = r["max_clock"]
                        recorded_fps = r["fps"]
                        hg.ImGuiText("Record infos: Duration: %.2f - FPS: %d" % (recorded_max_time - recorded_min_time, recorded_fps))

                if hg.ImGuiButton("Enter replay mode"):
                    request_new_state(main, "replay")

            elif recording:
                if hg.ImGuiButton("Stop recording"):
                    stop_record()
    hg.ImGuiEnd()

def update_gui_replay(main, keyboard):
    
    global selected_item_idx, recorded_min_time, recorded_max_time, timer, fps_record, current_id_play, selected_record, current_id_user, adding_user, user_name, user_info, recorded_fps, request_state
    
    if hg.ImGuiBegin("Dogfight - Replayer"):
        if not playing:
            
            c = conn.cursor()
            
            c.execute(f'''SELECT name, id_user FROM users''')
            r = c.fetchall()
            users = [(str(user[1]) +" - " + user[0]) for user in r]

            current_id_user -= 1
            f, current_id_user = hg.ImGuiCombo("Users", current_id_user, users)
            if f:
                selected_record = 0
            current_id_user += 1

            c.execute(f'''SELECT name FROM records WHERE id_user={current_id_user}''')
            r = c.fetchall()
            r = [x for xs in r for x in xs]
            selected_record = hg.ImGuiCombo("Records", selected_record, ["None"]+r)[1]

            if selected_record != 0:
                # get current id record
                c.execute(f'''SELECT id_rec FROM records WHERE id_user={current_id_user} AND name=\"{r[selected_record-1]}\"''')
                r = c.fetchone()
                if r is not None:
                    current_id_play = r["id_rec"]
                    
                c.execute(f'''SELECT max_clock, min_clock, fps FROM records WHERE id_rec={current_id_play}''')
                recorded_min_time = 0
                recorded_max_time = 0
                recorded_fps = 60
                r = c.fetchone()
                if r is not None:
                    recorded_min_time = r["min_clock"]
                    recorded_max_time = r["max_clock"]
                    recorded_fps = r["fps"]
                    hg.ImGuiText("Record infos: Duration: %.2f - FPS: %d" % (recorded_max_time - recorded_min_time, recorded_fps))

                if hg.ImGuiButton("Start play"):
                    start_play(main)
            
            if hg.ImGuiButton("Exit replay mode"):
                request_state = "disable"
        
        else:
            if recorded_max_time:
                timer = hg.ImGuiSliderFloat("Timeline", timer, recorded_min_time, recorded_max_time)[1]
            if pausing:
                lbl = "Resume"
            else:
                lbl = "Pause"
            if hg.ImGuiButton(lbl):
                pause_play()
            if pausing:
                if hg.ImGuiButton("< Prev frame") or keyboard.Pressed(hg.K_Sub):
                    timer -= 1/recorded_fps
                hg.ImGuiSameLine()
                if hg.ImGuiButton("Next frame >") or keyboard.Pressed(hg.K_Add):
                    timer += 1/recorded_fps
            if hg.ImGuiButton("Stop playing"):
                stop_play(main)
        
        # Items list:
        d, f = hg.ImGuiCheckbox("Display selected item", main.flag_display_selected_aircraft)
        if d: 
            main.flag_display_selected_aircraft = f
        if len(items_list) > 0:
            f, d = hg.ImGuiListBox("Items", selected_item_idx, items_names,20)
            if f:
                selected_item_idx = d
            if main.flag_display_selected_aircraft:
                main.selected_machine = items[items_names[selected_item_idx]]["i"]
        else:
            main.selected_machine = None
    
    hg.ImGuiEnd()

def update_gui_wait_request():
    if hg.ImGuiBegin("Dogfight - Recorder"):
        hg.ImGuiText("... Entering " + request_state + " mode ...")
    hg.ImGuiEnd()

def update_gui_disable():
    global request_state
    if hg.ImGuiBegin("Dogfight - Recorder"):
        
        hg.ImGuiText("Select a mission to record or enter replay mode")
        
        if hg.ImGuiButton("Enter replay mode"):
            request_state = "replay"
    hg.ImGuiEnd()

def update_gui_updating_database():
    if hg.ImGuiBegin("Dogfight - Recorder"):
        hg.ImGuiText("... Wait while writing in database ...")
        hg.ImGuiProgressBar(progress_cptr)
    hg.ImGuiEnd()

# Call this to lock recorder:

def request_new_state(main, req_state):
    global request_state
    request_state = req_state
    clear_items()
    if req_state == "disable":
        if recording:
            stop_record()
        elif playing:
            stop_play(main)
    elif req_state == "record":
        if playing:
            stop_play(main)
    elif req_state =="replay":
        if recording:
            stop_record()

# Call this when the scene to record/replay is ready:

def validate_requested_state():
    global state
    state = request_state


def update_gui(main,keyboard):

    if updating_database:
        update_gui_updating_database()
    elif state != request_state:
        update_gui_wait_request()
    elif state == "record":
        update_gui_record(main)
    elif state == "replay":
        update_gui_replay(main, keyboard)
    elif state == "disable":
        update_gui_disable()
    

def update(main, dt):
    global updating_database
    if updating_database:
        try:
            next(task_record_in_database)
        except StopIteration as stop:
            updating_database = False
    elif recording:
        update_recording(main, dt)
    elif playing:
        update_play(main, dt)
    

def before_quit_app():
    global conn
    if conn is not None:
        conn.commit()
        conn.close()
        conn = None


def serialize_machine_state(machine:Machines.Destroyable_Machine):
    if machine.type == Machines.Destroyable_Machine.TYPE_AIRCRAFT:
        return serialize_aircraft_state(machine)
    elif machine.type == Machines.Destroyable_Machine.TYPE_MISSILE:
        return serialize_missile_state(machine)
    elif machine.type == Machines.Destroyable_Machine.TYPE_MISSILE_LAUNCHER:
       return serialize_missile_launcher_state(machine)
    elif machine.type == Machines.Destroyable_Machine.TYPE_SHIP:
       return serialize_ship_state(machine)

def deserialize_machine_state(machine:Machines.Destroyable_Machine, s:str):
    if machine.type == Machines.Destroyable_Machine.TYPE_AIRCRAFT:
        deserialize_aircraft_state(machine, s)
    elif machine.type == Machines.Destroyable_Machine.TYPE_MISSILE:
        deserialize_missile_state(machine, s)
    elif machine.type == Machines.Destroyable_Machine.TYPE_MISSILE_LAUNCHER:
        deserialize_missile_launcher_state(machine, s)
    elif machine.type == Machines.Destroyable_Machine.TYPE_SHIP:
        deserialize_ship_state(machine, s)
    

def serialize_missile_state(machine:Machines.Missile):
    matrix = dc.serialize_mat4(machine.get_parent_node().GetTransform().GetWorld())
    v_move = dc.serialize_vec3(machine.get_move_vector())
    wreck = dc.serialize_boolean(machine.wreck)
    return matrix + ":" + v_move + ":" + wreck

def serialize_aircraft_state(machine:Machines.Aircraft):
    matrix = dc.serialize_mat4(machine.get_parent_node().GetTransform().GetWorld())
    v_move = dc.serialize_vec3(machine.get_move_vector())
    health_lvl = str(machine.get_health_level())
    wreck = dc.serialize_boolean(machine.wreck)
    brake_level = str(machine.get_brake_level())
    flaps_level = str(machine.get_flaps_level())
    landed = dc.serialize_boolean(machine.flag_landed)
    td = machine.get_device("TargettingDevice")
    if td is not None:
        target_name = td.get_target_name()
    else:
        target_name = None
    if target_name is None:
        target_name = str(target_name)
    return matrix +":"+ v_move +":"+ health_lvl + ":" + wreck + ":" + brake_level + ":" + flaps_level + ":" + landed + ":" + target_name



def serialize_missile_launcher_state(machine:MissileLauncherS400):
    matrix = dc.serialize_mat4(machine.get_parent_node().GetTransform().GetWorld())
    wreck = dc.serialize_boolean(machine.wreck)
    return matrix + ":" + wreck

def serialize_ship_state(machine:Machines.Carrier):
    matrix = dc.serialize_mat4(machine.get_parent_node().GetTransform().GetWorld())
    wreck = dc.serialize_boolean(machine.wreck)
    return matrix + ":" + wreck


def deserialize_aircraft_state(machine:Machines.Aircraft, s:str):
    f = s.split(":")
    matrix = dc.deserialize_mat4(f[0])
    machine.v_move = dc.deserialize_vec3(f[1])
    machine.wreck = bool(f[3])
    health_lvl = float(f[2])
    machine.get_parent_node().GetTransform().SetWorld(matrix)
    machine.set_health_level(health_lvl)
    machine.reset_brake_level(float(f[4]))
    machine.reset_flaps_level(float(f[5]))
    machine.flag_landed = bool(f[6])
    td = machine.get_device("TargettingDevice")
    if td is not None:
        td.set_target_by_name(f[7])

def deserialize_missile_state(machine:Machines.Missile, s:str):
    f = s.split(":")
    matrix = dc.deserialize_mat4(f[0])
    machine.v_move = dc.deserialize_vec3(f[1])
    machine.wreck = bool(f[2])
    machine.get_parent_node().GetTransform().SetWorld(matrix)

def deserialize_ship_state(machine:Machines.Carrier, s:str):
    f = s.split(":")
    machine.wreck = bool(f[1])
    matrix = dc.deserialize_mat4(f[0])
    machine.get_parent_node().GetTransform().SetWorld(matrix)

def deserialize_missile_launcher_state(machine:MissileLauncherS400, s:str):
    f = s.split(":")
    machine.wreck = bool(f[1])
    matrix = dc.deserialize_mat4(f[0])
    machine.get_parent_node().GetTransform().SetWorld(matrix)