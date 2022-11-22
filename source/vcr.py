#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2017-2020 Thomas Simonnet, Movida Production.
import json
import os

import harfang as hg
from datetime import datetime
import data_converter as dc
import sqlite3

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
render_head = False
timer = 0
previous_timer = 0
recorded_max_time = 0
recorded_fps = 60

items = {}
items_list = []
selected_record = 0
records = None
last_value_recorded = {}

items_words_list = ["world", "int", "float"]

fps_record = 60

#item: hg.Node
#params: "world", "pos", "mat4", "enable", "float", "int", "bool", "str"
#container: if not None, contain the value to record
def AddItem(item, params=[], name=None, container=None):
    global items, items_list
    if isinstance(item, hg.Node) and name is None:
        name = f"{item.GetName()} {item.GetTransform().GetPos().x:.2}{item.GetTransform().GetPos().y:.2}{item.GetTransform().GetPos().z:.2}"
    elif isinstance(item, str) and name is None:
        name = item

    name = dc.conform_string(name)
    #print("VCR - add item " + name)
    items[name] = {"i": item, "params": params, "container": container, "recording": True}
    
    items_list.append(items[name])
    return items[name]


def post_load_env():
    global conn, items_list, selected_record

    items_list = []

    # check everything is set
    if conn is None:
        conn = sqlite3.connect('database.db')
        conn.row_factory = sqlite3.Row
        print("VCR - database connected")

        c = conn.cursor()

        c.execute(f'''SELECT name FROM sqlite_master WHERE type='table' AND name='users';''')
        table_users_exists = c.fetchone()

        c.execute('''CREATE TABLE IF NOT EXISTS users(id_user INTEGER PRIMARY KEY, name TEXT, info TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS records(id_rec INTEGER PRIMARY KEY, name TEXT, max_clock FLOAT, fps INT, id_user INTEGER REFERENCES users, CONSTRAINT fk_users FOREIGN KEY (id_user) REFERENCES users(id_user) ON DELETE CASCADE)''')
        
        # add default user
        if table_users_exists is None:
            c.execute("INSERT INTO users(name, info) VALUES (\"Default\", ?)", ["HARFANG NWSC User"])
        conn.commit()

    selected_record = 0


def start_record(name_record):
    global recording, records, timer, current_id_rec, last_value_recorded
    
    # check if we are already start
    if recording:
        return

    recording = True
    records = None
    last_value_recorded = {}
    timer = 0

    # add record
    c = conn.cursor()
    #c.execute(f'''SELECT id_rec FROM records WHERE id_user={current_id_user} AND name=\"{name_record}\"''')
    #r = c.fetchone()
    #if r is None:
    # insert the new record
    c.execute(f'''INSERT INTO records(id_user, name, fps) VALUES ({current_id_user}, \"{name_record}\", {fps_record})''')
    c.execute(f'''SELECT id_rec FROM records WHERE id_user={current_id_user} AND name=\"{name_record}\"''')
    r = c.fetchone()
            
    if r is not None:
        current_id_rec = r["id_rec"]
    conn.commit()
    print(f"create record: {name_record}, {current_id_rec}")
    

def stop_record():
    global recording
    
    # check if we are already stopped
    if not recording:
        return

    recording = False
    c = conn.cursor()

    # save the current record
    # create db for items
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

    # add value to items
    for t, record in records.items():
        for name, value in record.items():
            c.execute(f"INSERT INTO {name}(id_rec, c, v) VALUES ({current_id_rec}, {t}, \"{value}\");")
    
    print(str(current_id_rec))
    c.execute(f"UPDATE records SET max_clock={timer} WHERE id_rec={current_id_rec};")
    print(str(current_id_rec))
    #c.execute(f"UPDATE records SET fps={fps_record} WHERE id_rec={current_id_rec};")
    conn.commit()


def update_recording(dt):
    global records, timer, previous_timer, last_value_recorded
    if records is None:
        records = {}
        timer = 0
        previous_timer = 0

    if timer - previous_timer > 1.0 / fps_record:
        print(str(fps_record) + " " + str(timer))
        record = {}
        for name, params in items.items():
            if not params["recording"]:
                continue
            item = params["i"]
            for p in params["params"]:
                v = ""
                n = f"{name}_{p}"
                if p == "world":
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
                elif p in "str":
                    v = item
                else:
                    v = eval(p["save"])
                    n = f"{name}_{p['i']}"
                if n not in last_value_recorded or (n in last_value_recorded and v != last_value_recorded[n]):
                    last_value_recorded[n] = record[n] = v

        records[timer] = record
        previous_timer = timer
    timer += hg.time_to_sec_f(dt)


def start_play(scene):
    global playing, timer
    
    timer = 0
    playing = True


def stop_play(scene):
    global playing, pausing
    playing = False
    pausing = False

def pause_play():
    global pausing
    pausing = not pausing


def update_play(scene, dt):
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
            if p not in items_words_list:
                n = f"{name}_{p['n']}"
            
            c.execute(f"SELECT v FROM {n} where id_rec={current_id_play} and c <= {timer} ORDER BY c DESC LIMIT 1;")
            r = c.fetchone()
            if r is not None:
                v = r["v"]
                if p == "world":
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

    if timer > recorded_max_time:
        stop_play(scene)


def update_gui(scene, keyboard):
    global recorded_max_time, timer, fps_record, current_id_play, selected_record, current_id_user, adding_user, user_name, user_info, recorded_fps
    
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

        if not playing and not recording:
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

            if hg.ImGuiButton("Start recording"):
                name_record = datetime.now().strftime("%m/%d/%Y_%H:%M:%S")
                start_record(dc.conform_string(name_record))
            
            fps_record = int(hg.ImGuiSliderFloat("Recording FPS", fps_record, 1, 128)[1])

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
                    
                c.execute(f'''SELECT max_clock, fps FROM records WHERE id_rec={current_id_play}''')
                recorded_max_time = 0
                recorded_fps = 60
                r = c.fetchone()
                if r is not None:
                    recorded_max_time = r["max_clock"]
                    recorded_fps = r["fps"]
                    hg.ImGuiText("Record infos: Duration: %.2f - FPS: %d" % (recorded_max_time, recorded_fps))

                if hg.ImGuiButton("Start play"):
                    start_play(scene)

        elif recording:
            if hg.ImGuiButton("Stop recording"):
                stop_record()
        
        elif playing:
            if recorded_max_time:
                timer = hg.ImGuiSliderFloat("Timeline", timer, 0, recorded_max_time)[1]
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
                stop_play(scene)

def update(scene, dt):
    if recording:
        update_recording(dt)
    elif playing:
        update_play(scene, dt)


def before_quit_app():
    global conn
    if conn is not None:
        conn.commit()
        conn.close()
        conn = None