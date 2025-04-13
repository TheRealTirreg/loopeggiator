# save_load.py
import json
import os
from PySide6.QtWidgets import QFileDialog
from arp import Mode

def save_project(main_window, filename=None):
    if not filename:
        save_dir = os.path.join(os.path.dirname(__file__), "saves")
        os.makedirs(save_dir, exist_ok=True)
        filename, _ = QFileDialog.getSaveFileName(main_window, "Save Project", save_dir, "JSON Files (*.json)")
        if not filename:
            return

    if not filename.endswith(".json"):
        filename += ".json"

    data = {
        "bpm": main_window.top_bar.bpm,
        "instruments": []
    }

    for row in main_window.instrument_rows:
        row_data = {
            "mute": row.mute_checkbox.isChecked(),
            "volume": row.settings_panel.volume_slider.value(),
            "instrument": row.instrument,
            "arpeggiators": []
        }

        for block in row.arp_blocks:
            arp = block.arp_widget.arp
            block_data = {
                "rate": arp.rate,
                "note_length": arp.note_length,
                "ground_note": arp.ground_note,
                "mute_ground_note": arp.mute_ground_note,
                "mode": arp.mode.name if arp.mode else None,
                "mute": arp.mute,
                "velocity": arp.velocity,
                "variants_active": arp.variants_active,
                "variants": arp.variants,
                "chords_active": arp.chords_active,
                "vibrato": arp.vibrato,
                "reverb": arp.reverb,
                "chorus": arp.chorus
            }
            row_data["arpeggiators"].append(block_data)

        data["instruments"].append(row_data)

    with open(filename, "w") as f:
        json.dump(data, f, indent=2)

def load_project(main_window, filename=None):
    if not filename:
        save_dir = os.path.join(os.path.dirname(__file__), "saves")
        os.makedirs(save_dir, exist_ok=True)
        filename, _ = QFileDialog.getOpenFileName(main_window, "Load Project", save_dir, "JSON Files (*.json)")
        if not filename:
            return

    if not os.path.isfile(filename):
        print(f"Project file not found: {filename}")
        return

    with open(filename, "r") as f:
        data = json.load(f)

    main_window.top_bar.bpm = data.get("bpm", 60)

    for row in list(main_window.instrument_rows):
        main_window.del_instrument(row)

    for i, row_data in enumerate(data.get("instruments", [])):
        row = main_window.add_instrument()
        if row is None:
            print(f"Failed to add instrument row {i}.")
            continue

        row.mute_checkbox.setChecked(row_data.get("mute", False))
        row.settings_panel.volume_slider.setValue(row_data.get("volume", 64))

        target_program = row_data.get("instrument", 0)

        # Find the index of the first preset with this program number
        preset_index = next(
            (i for i in range(row.settings_panel.instrument_combo.count())
            if row.settings_panel.instrument_combo.itemData(i).get("program") == target_program),
            0
        )

        row.settings_panel.instrument_combo.setCurrentIndex(preset_index)

        if row.arp_blocks:
            row.remove_arp_block(row.arp_blocks[0])

        for block_data in row_data.get("arpeggiators", []):
            row.arp_panel.add_block(
                mute=block_data.get("mute", False),
                rate=block_data.get("rate", 1.0),
                note_length=block_data.get("note_length", 0.2),
                ground_note=block_data.get("ground_note", 60),
                mute_ground_note=block_data.get("mute_ground_note", False),
                mode=Mode[block_data.get("mode")] if block_data.get("mode") in Mode.__members__ else None,
                variants_active=block_data.get("variants_active", [False, False, False]),
                variants=block_data.get("variants", [0, 0, 0]),
                chords_active=block_data.get("chords_active", [False, False, False]),
            )

            block = row.arp_blocks[-1]
            arp = block.arp_widget.arp

            arp.vibrato = block_data.get("vibrato", False)
            block.arp_widget.vibrato_checkbox.setChecked(arp.vibrato)

            arp.reverb = block_data.get("reverb", False)
            block.arp_widget.reverb_checkbox.setChecked(arp.reverb)

            arp.chorus = block_data.get("chorus", False)
            block.arp_widget.chorus_checkbox.setChecked(arp.chorus)

            arp.velocity = block_data.get("velocity", 100)
            row.update_arp_volumes()

            block.arp_widget.set_variants(arp.variants_active, arp.variants)
            block.arp_widget.update_chord_button_states()

    main_window.update_loop_length()
