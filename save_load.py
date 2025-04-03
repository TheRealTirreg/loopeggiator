import json
import os
from PySide6.QtWidgets import QFileDialog
from arp import Mode

def save_project(main_window, filename=None):
    # Create saves folder if needed (only if no filename provided)
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
            "volume": row.volume_slider.value(),
            "instrument": row.instrument,
            "arpeggiators": []
        }

        for block in row.arp_blocks:
            arp = block.arp_widget.arp
            block_data = {
                "loop_count": block.loop_spin.value(),
                "rate": arp.rate,
                "note_length": arp.note_length,
                "ground_note": arp.ground_note,
                "mode": arp.mode.name,
                "mute": arp.mute,
                "velocity": arp.velocity,
                "variants_active": arp.variants_active,
                "variants": arp.variants
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

    # Set BPM (use setter or method depending on your implementation)
    bpm_value = data.get("bpm", 60)  # Default BPM is 60
    main_window.top_bar.bpm = bpm_value

    # Remove existing rows first
    for row in list(main_window.instrument_rows):
        main_window.del_instrument(row)

    # Rebuild instrument rows
    for i, row_data in enumerate(data.get("instruments", [])):
        row = main_window.add_instrument()
        if row is None:
            print(f"Failed to add instrument row {i}.")
            continue  # Just skip this row if something went wrong for now

        row.mute_checkbox.setChecked(row_data.get("mute", False))
        row.volume_slider.setValue(row_data.get("volume", 64))
        row.instrument_combo.setCurrentIndex(
            row.instrument_combo.findData(row_data.get("instrument", 0))
        )
        row.change_instrument(row.instrument_combo.currentIndex())

        # Remove initial default arp if it exists
        if row.arp_blocks:
            row.remove_arp_block(row.arp_blocks[0])

        for block_data in row_data.get("arpeggiators", []):
            row.add_arpeggiator_block(repetitions=block_data.get("loop_count", 1))
            block = row.arp_blocks[-1]
            arp = block.arp_widget.arp

            # Set core arpeggiator settings
            arp.rate = block_data.get("rate", 1)
            block.arp_widget.rate_spin.setValue(arp.rate)

            arp.note_length = block_data.get("note_length", 1)
            block.arp_widget.note_length_spin.setValue(arp.note_length)

            arp.ground_note = block_data.get("ground_note", 60)
            block.arp_widget.ground_note_spin.setValue(arp.ground_note)

            # Restore mode with fallback to UP
            mode_str = block_data.get("mode", "UP")
            try:
                mode = Mode[mode_str]
            except KeyError:
                mode = Mode.UP
            arp.mode = mode
            block.arp_widget.set_mode(mode)

            # Mute & velocity
            arp.mute = block_data.get("mute", False)
            block.arp_widget.mute_checkbox.setChecked(arp.mute)

            arp.velocity = block_data.get("velocity", 100)
            row.update_arp_volumes()  # ensure consistency

            # Restore variant state safely
            va = block_data.get("variants_active", [False, False, False])
            v = block_data.get("variants", [0, 0, 0])
            arp.variants_active = va
            arp.variants = v

            # Also reapply visual states safely
            block.arp_widget.set_variants(arp.variants_active, arp.variants)

    main_window.update_loop_length()
