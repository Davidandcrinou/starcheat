"""
GUI module for starcheat
"""

import sys, re, os
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QApplication, QDialog, QMainWindow, QTableWidget
from PyQt5.QtWidgets import QFileDialog, QTableWidgetItem, QMessageBox
from PyQt5.QtGui import QPixmap, QIcon, QImageReader

import save_file, assets, config
import qt_mainwindow, qt_itemedit, qt_itembrowser, qt_blueprints, qt_options, qt_openplayer

conf = config.Config().read()

# TODO: it might be almost time to split this into a file per dialog

def inv_icon(item_name):
    """Return a QPixmap object of the inventory icon of a given item (if possible)."""
    icon_file = assets.Items().get_item_icon(item_name)

    if icon_file == None:
        return QPixmap()

    reader = QImageReader(icon_file[0])
    reader.setClipRect(QtCore.QRect(icon_file[1], 0, 16, 16))
    return QPixmap.fromImageReader(reader).scaled(32, 32)

def empty_slot():
    """Return an empty bag slot widget."""
    return ItemWidget(save_file.empty_slot())

# TODO: a decision needs to be made here whether to continue with the custom
#       widget item or an entirely new custom table view. if the features below
#       are easy enough to add then we'll just stick with the current method
# TODO: swap items instead of overwriting
#       apparently this is done by reimplementing the drag functions
# TODO: some sort of icon painter so we can show a frame, rarity and count overlay
class ItemWidget(QTableWidgetItem):
    """Custom table wiget item with icon support and extra item variables."""
    def __init__(self, item):
        self.name = item[0]
        self.item_count = item[1]
        self.variant = item[2]
        QTableWidgetItem.__init__(self, self.name)
        self.setTextAlignment(QtCore.Qt.AlignCenter)

        if self.name != "":
            self.setToolTip(self.name + " (" + str(self.item_count) + ")")
        else:
            return

        icon = inv_icon(self.name)
        try:
            self.setIcon(QtGui.QIcon(icon))
        except TypeError:
            pass

        if type(icon) is QPixmap:
            #self.setText(str(self.item_count))
            self.setText("")

def pretty_variant(variant):
    variant_type = variant[0]
    variant_value = variant[1]
    if variant_type == 2:
        return str(variant_value[0])
    elif variant_type == 3:
        if variant_value[0] == 1:
            return "True"
        else:
            return "False"
    elif variant_type == 4:
        return str(variant_value)
    elif variant_type == 5:
        return '"' + str(variant_value) + '"'
    elif variant_type == 6:
        items = []
        for i in variant_value:
            items.append(pretty_variant(i))
        return ", ".join(items)
    elif variant_type == 7:
        items = []
        for i in variant_value:
            items.append(i[0] + ": {" + pretty_variant(i[1]) + "}")
        return ", ".join(items)
    else:
        return "__UNKNOWN_TYPE__"

class ItemVariant(QTableWidgetItem):
    def __init__(self, variant):
        # TODO: remove prints when this is fleshed out
        print(variant)
        self.variant_name = variant[0]
        self.variant_type = variant[1][0]
        self.variant_value = variant[1][1]

        item_text = self.variant_name + ": " + pretty_variant(variant[1])
        QTableWidgetItem.__init__(self, item_text)
        self.setToolTip(item_text)

        if self.variant_type == 2:
            print(2)
        elif self.variant_type == 3:
            print(3)
        elif self.variant_type == 4:
            print(4)
        elif self.variant_type == 5:
            print(5)
        elif self.variant_type == 6:
            print(6)
        elif self.variant_type == 7:
            print(7)

class ItemBrowser():
    def __init__(self, parent):
        """Dialog for viewing/searching indexed items and returning selection."""
        self.dialog = QDialog(parent)
        self.item_browser = qt_itembrowser.Ui_Dialog()
        self.item_browser.setupUi(self.dialog)

        self.item_browse_select = None
        self.items = assets.Items()

        # populate category combobox
        for cat in self.items.get_categories():
            self.item_browser.category.addItem(cat[0])

        # populate initial items list
        self.item_browser.items.clear()
        for item in self.items.get_all_items():
            self.item_browser.items.addItem(item[0])

        self.item_browser.items.itemSelectionChanged.connect(self.update_item_view)
        self.item_browser.filter.textChanged.connect(self.update_item_list)
        self.item_browser.category.currentTextChanged.connect(self.update_item_list)

        self.item_browser.items.setCurrentRow(0)
        self.item_browser.filter.setFocus()

    def update_item_view(self):
        """Update item details view with data from currently selected item."""
        try:
            selected = self.item_browser.items.selectedItems()[0].text()
        except IndexError:
            return

        item = self.items.get_item(selected)
        # don't like so many queries but should be ok for the browser
        icon_file = self.items.get_item_image(selected)
        # fallback on inventory icon
        if icon_file == None:
            icon = inv_icon(selected)
        else:
            icon = QPixmap(icon_file).scaledToHeight(64)

        # last ditch, just use x.png
        try:
            self.item_browser.item_icon.setPixmap(icon)
        except TypeError:
            self.item_browser.item_icon.setPixmap(QPixmap(self.items.missing_icon()))

        self.item_browse_select = selected

        # TODO: update qt objectnames, already not making sense
        try:
            self.item_browser.item_name.setText(item[0]["shortdescription"])
        except KeyError:
            self.item_browser.item_name.setText("Missing short description")

        try:
            self.item_browser.short_desc.setText(item[0]["description"])
        except KeyError:
            self.item_browser.short_desc.setText("Missing description")

        # populate default variant table
        row = 0
        self.item_browser.info.setRowCount(len(item[0]))
        for key in item[0]:
            try:
                text = str(key) + ": " + str(item[0][key])
                table_item = QTableWidgetItem(text)
                table_item.setToolTip(text)
                self.item_browser.info.setItem(row, 0, table_item)
            except TypeError:
                pass
            row += 1

    def update_item_list(self):
        """Populate item list based on current filter details."""
        category = self.item_browser.category.currentText()
        name = self.item_browser.filter.text()
        result = self.items.filter_items(category, name)

        # TODO: i'd like this to set focus on the list when category is changed
        #       but not when the edit box is changed (split this function)
        self.item_browser.items.clear()
        for item in result:
            self.item_browser.items.addItem(item[0])
        self.item_browser.items.setCurrentRow(0)

    def get_selection(self):
        return self.item_browse_select

class ItemEdit():
    def __init__(self, parent, item=None):
        """Takes an item widget and displays an edit dialog for it."""
        self.item_dialog = QDialog(parent)
        self.item_edit = qt_itemedit.Ui_Dialog()
        self.item_edit.setupUi(self.item_dialog)

        self.item_browser = None

        # cells don't retain ItemSlot widget when they've been dragged away
        if type(item) is QTableWidgetItem or item == None:
            self.item = empty_slot()
        else:
            self.item = item

        # set up signals
        self.item_edit.load_button.clicked.connect(self.new_item_browser)
        self.item_edit.item_type.textChanged.connect(self.update_item)

        # set name text box
        self.item_edit.item_type.setText(self.item.name)
        # set item count spinbox
        self.item_edit.count.setValue(int(self.item.item_count))

        # set up variant table
        self.item_edit.variant.setRowCount(len(self.item.variant[1]))
        for i in range(len(self.item.variant[1])):
            variant = ItemVariant(self.item.variant[1][i])
            self.item_edit.variant.setItem(i, 0, variant)

        self.item_edit.item_type.setFocus()

        self.item_dialog.show()

        # if the inventory slot is empty show the browser as well
        if self.item.name == "":
            self.new_item_browser()

    def update_item(self):
        """Update main item view with current item data."""
        name = self.item_edit.item_type.text()

        try:
            item = assets.Items().get_item(name)
        except TypeError:
            self.item_edit.short_desc.setText("")
            self.item_edit.desc.setText("")
            self.item_edit.icon.setPixmap(QPixmap())
            return

        try:
            self.item_edit.short_desc.setText(item[0]["shortdescription"])
        except KeyError:
            self.item_edit.short_desc.setText("Missing short description")

        try:
            self.item_edit.desc.setText(item[0]["description"])
        except KeyError:
            self.item_edit.desc.setText("Missing description")

        try:
            self.item_edit.icon.setPixmap(inv_icon(name))
        except TypeError:
            # TODO: change this to the x.png?
            self.item_edit.icon.setPixmap(QPixmap())

    def get_item(self):
        """Return an ItemWidget of the currently open item."""
        type_name = self.item_edit.item_type.text()
        count = self.item_edit.count.value()
        variant = self.item.variant
        return ItemWidget((type_name, count, variant))

    def new_item_browser(self):
        self.item_browser = ItemBrowser(self.item_dialog)
        self.item_browser.dialog.accepted.connect(self.set_item_browser_selection)
        self.item_browser.dialog.show()

    def set_item_browser_selection(self):
        self.item_edit.item_type.setText(self.item_browser.get_selection())
        # TODO: stuff like setting value max to maxstack
        self.item_edit.count.setValue(1)

class BlueprintLib():
    def __init__(self, parent, known_blueprints):
        """Blueprint library management dialog."""
        self.dialog = QDialog(parent)
        self.blueprint_lib = qt_blueprints.Ui_Dialog()
        self.blueprint_lib.setupUi(self.dialog)

        self.blueprints = assets.Blueprints()
        self.known_blueprints = known_blueprints

        # populate known list
        self.blueprint_lib.known_blueprints.clear()
        for blueprint in self.known_blueprints:
            self.blueprint_lib.known_blueprints.addItem(blueprint)

        # populate initial available list
        self.blueprint_lib.available_blueprints.clear()
        for blueprint in self.blueprints.get_all_blueprints():
            self.blueprint_lib.available_blueprints.addItem(blueprint[0])

        # populate category combobox
        for cat in self.blueprints.get_categories():
            self.blueprint_lib.category.addItem(cat[0])

        self.blueprint_lib.add_button.clicked.connect(self.add_blueprint)
        self.blueprint_lib.remove_button.clicked.connect(self.remove_blueprint)

        self.blueprint_lib.filter.textChanged.connect(self.update_available_list)
        self.blueprint_lib.category.currentTextChanged.connect(self.update_available_list)

        self.blueprint_lib.filter.setFocus()

    def update_available_list(self):
        """Populate available blueprints list based on current filter details."""
        category = self.blueprint_lib.category.currentText()
        name = self.blueprint_lib.filter.text()
        result = self.blueprints.filter_blueprints(category, name)
        self.blueprint_lib.available_blueprints.clear()
        for blueprint in result:
            self.blueprint_lib.available_blueprints.addItem(blueprint[0])
        self.blueprint_lib.available_blueprints.setCurrentRow(0)

    def add_blueprint(self):
        """Add currently select blueprint in available list to known list."""
        try:
            selected = self.blueprint_lib.available_blueprints.currentItem().text()
        except AttributeError:
            # nothing selected
            return

        # don't add more than one of each blueprint
        if selected in self.known_blueprints:
            return

        # insert the new item and regenerate the list
        self.known_blueprints.append(selected)
        self.known_blueprints.sort()
        self.blueprint_lib.known_blueprints.clear()
        for i in range(len(self.known_blueprints)):
            self.blueprint_lib.known_blueprints.addItem(self.known_blueprints[i])
            if self.known_blueprints[i] == selected:
                self.blueprint_lib.known_blueprints.setCurrentRow(i)

    def remove_blueprint(self):
        """Remove currently selected blueprint in known list."""
        try:
            selected = self.blueprint_lib.known_blueprints.currentItem().text()
        except AttributeError:
            return

        # remove item and regen list
        self.known_blueprints.remove(selected)
        self.known_blueprints.sort()
        self.blueprint_lib.known_blueprints.clear()
        for blueprint in self.known_blueprints:
            self.blueprint_lib.known_blueprints.addItem(blueprint)

    def get_known_list(self):
        return self.known_blueprints

class OptionsDialog():
    def __init__(self, parent):
        # TODO: all the other dialogs should match this naming style
        self.dialog = QDialog(parent)
        self.ui = qt_options.Ui_Dialog()
        self.ui.setupUi(self.dialog)

        # read the current config and prefill everything
        self.config = config.Config().read()
        self.ui.assets_folder.setText(self.config["assets_folder"])
        self.ui.player_folder.setText(self.config["player_folder"])
        # TODO: do backups
        self.ui.backup_folder.setText(self.config["backup_folder"])

        self.ui.assets_folder_button.clicked.connect(self.open_assets)
        self.ui.player_folder_button.clicked.connect(self.open_player)
        self.ui.backup_folder_button.clicked.connect(self.open_backup)
        self.ui.rebuild_button.clicked.connect(self.rebuild_db)

    def write(self):
        self.config["assets_folder"] = self.ui.assets_folder.text()
        self.config["player_folder"] = self.ui.player_folder.text()
        self.config["backup_folder"] = self.ui.backup_folder.text()
        config.Config().write(self.config)

    def open_assets(self):
        filename = QFileDialog.getExistingDirectory(self.dialog,
                                               "Choose assets folder...",
                                               self.config["assets_folder"])
        if filename != "": self.ui.assets_folder.setText(filename)

    def open_player(self):
        filename = QFileDialog.getExistingDirectory(self.dialog,
                                               "Choose player save folder...",
                                               self.config["player_folder"])
        if filename != "": self.ui.player_folder.setText(filename)

    def open_backup(self):
        filename = QFileDialog.getExistingDirectory(self.dialog,
                                               "Choose backup location...",
                                               self.config["backup_folder"])
        if filename != "": self.ui.backup_folder.setText(filename)

    def rebuild_db(self):
        self.write()
        if os.path.isfile(self.config["assets_db"]):
            os.remove(self.config["assets_db"])
        db = assets.AssetsDb()
        # TODO: i want some feedback here

class CharacterSelectDialog():
    def __init__(self, parent):
        self.dialog = QDialog(parent)
        self.ui = qt_openplayer.Ui_OpenPlayer()
        self.ui.setupUi(self.dialog)

        self.dialog.accepted.connect(self.accept)
        self.dialog.rejected.connect(sys.exit)

        self.get_players()

        self.populate()


    def accept(self):
        ply = self.ui.listWidget.selectedItems()[0].text()
        if ply != "":
            self.selected = self.players[ply]
            self.dialog.close()

    def get_players(self):
        players_found = {}
        for root, dirs, files in os.walk(config.Config().read()["player_folder"]):
            for f in files:
                #is there need for regular expressions at this point?
                if f.endswith(".player"):
                    try:
                        ply = save_file.PlayerSave(os.path.join(root, f))
                        players_found[ply.get_name()] = ply
                    except save_file.WrongSaveVer:
                        #ignores players that cannot be loaded
                        print("{} could not be loaded due to being incompatible with this version of starcheat.".format(ply.get_name()))
                        #pop the player if it's incompatible
                        #I didn't expect the dictionary to still hold the player if execution hits the exception block
                        #I still don't expect it, hence the try. Just in case this is odd behavior.
                        try:
                            players_found.pop(ply.get_name())
                        except KeyError:
                            pass

        self.players = players_found

    def populate(self):
        for player in self.players.keys():
            self.ui.listWidget.addItem(player)

    def show(self):
        #quit if there are no players
        if len(self.players) == 0:
            dialog = QMessageBox()
            msg = "No save files found that are compatible with this version of starcheat."
            dialog.setText(msg)
            dialog.exec()
            sys.exit();
        else:
            self.dialog.exec()


class MainWindow():
    def __init__(self):
        """Display the main starcheat window."""
        self.app = QApplication(sys.argv)
        self.window = QMainWindow()
        self.ui = qt_mainwindow.Ui_MainWindow()
        self.ui.setupUi(self.window)

        # launch first setup
        self.setup_dialog = None
        try:
            open(conf["assets_db"])
        except FileNotFoundError:
            self.new_setup_dialog()

        self.filename = None
        self.items = assets.Items()

        # atm we only support one of each dialog at a time, don't think this
        # will be a problem tho
        # TODO: some really weird behaviour here w/ blueprint
        #self.item_browser = None
        self.item_edit = None
        self.blueprint_lib = None
        self.options_dialog = None

        # populate race combo box
        for race in save_file.race_types:
            self.ui.race.addItem(race)

        # connect action menu
        self.ui.actionSave.triggered.connect(self.save)
        self.ui.actionReload.triggered.connect(self.reload)
        self.ui.actionOpen.triggered.connect(self.open_file)
        self.ui.actionQuit.triggered.connect(self.app.closeAllWindows)
        self.ui.actionOptions.triggered.connect(self.new_options_dialog)

        # launch open file dialog
        # we want this after the races are populated but before the slider setup
        if self.open_file() == False:
            return

        # set up sliders to update values together
        stats = "health", "energy", "food", "warmth", "breath"
        for s in stats:
            update = getattr(self, "update_" + s)
            getattr(self.ui, s).valueChanged.connect(update)
            getattr(self.ui, "max_" + s).valueChanged.connect(update)

        # set up bag tables
        bags = "wieldable", "head", "chest", "legs", "back", "main_bag", "action_bar", "tile_bag"
        for b in bags:
            item_edit = getattr(self, "new_" + b + "_item_edit")
            getattr(self.ui, b).cellDoubleClicked.connect(item_edit)

        self.ui.blueprints_button.clicked.connect(self.new_blueprint_edit)
        self.ui.name.setFocus()

        self.window.show()
        sys.exit(self.app.exec_())

    def update(self):
        """Update all GUI widgets with values from PlayerSave instance."""
        # uuid / save version
        self.ui.uuid_label.setText(self.player.get_uuid())
        self.ui.ver_label.setText("v" + self.player.get_save_ver())
        # name
        self.ui.name.setText(self.player.get_name())
        # race
        self.ui.race.setCurrentText(self.player.get_race())
        # pixels
        self.ui.pixels.setValue(self.player.get_pixels())
        # description
        self.ui.description.setPlainText(self.player.get_description())
        # gender
        getattr(self.ui, self.player.get_gender()).toggle()

        # stats
        stats = "health", "energy", "food", "breath"
        for stat in stats:
            max_stat = getattr(self.player, "get_max_" + stat)()
            getattr(self.ui, "max_" + stat).setValue(max_stat)
            cur_stat = getattr(self.player, "get_" + stat)()
            getattr(self.ui, stat).setMaximum(cur_stat[1])
            getattr(self.ui, stat).setValue(cur_stat[0])
            getattr(self, "update_" + stat)()
        # energy regen rate
        self.ui.energy_regen.setValue(self.player.get_energy_regen())
        # warmth
        max_warmth = self.player.get_max_warmth()
        self.ui.max_warmth.setValue(max_warmth)
        cur_warmth = self.player.get_warmth()
        self.ui.warmth.setMinimum(cur_warmth[0])
        self.ui.warmth.setMaximum(max_warmth)
        self.ui.warmth.setValue(cur_warmth[1])
        self.update_warmth()

        # equipment
        equip_bags = "head", "chest", "legs", "back"
        for bag in equip_bags:
            items = [ItemWidget(x) for x in getattr(self.player, "get_" + bag)()]
            getattr(self.ui, bag).setItem(0, 0, items[0])
            getattr(self.ui, bag).setItem(0, 1, items[1])

        # wielded
        self.update_bag("wieldable")

        # bags
        self.update_bag("main_bag")
        self.update_bag("tile_bag")
        self.update_bag("action_bar")

    def save(self):
        """Update internal player dict with GUI values and export to file."""
        # name
        self.player.set_name(self.ui.name.text())
        # race
        self.player.set_race(self.ui.race.currentText())
        # pixels
        self.player.set_pixels(self.ui.pixels.value())
        # description
        self.player.set_description(self.ui.description.toPlainText())

        # gender
        if self.ui.male.isChecked():
            self.player.set_gender("male")
        else:
            self.player.set_gender("female")

        # stats
        stats = "health", "energy", "food", "breath"
        for s in stats:
            current = getattr(self.ui, s).value()
            maximum = getattr(self.ui, "max_" + s).value()
            getattr(self.player, "set_" + s)(current, maximum)
            getattr(self.player, "set_max_" + s)(maximum)
        # energy regen rate
        self.player.set_energy_regen(self.ui.energy_regen.value())
        # warmth
        self.player.set_warmth(self.ui.warmth.value())
        self.player.set_max_warmth(self.ui.max_warmth.value())

        # equipment
        equip_bags = "head", "chest", "legs", "back"
        for b in equip_bags:
            bag = self.get_equip(b)
            getattr(self.player, "set_" + b)(bag[0], bag[1])

        # bags
        bags = "wieldable", "main_bag", "tile_bag", "action_bar"
        for b in bags:
            getattr(self.player, "set_" + b)(self.get_bag(b))

        # save and show status
        self.player.dump()
        self.player.export_save(self.player.filename)
        self.ui.statusbar.showMessage("Saved " + self.player.filename, 3000)

    def new_item_edit(self, bag):
        """Display a new item edit dialog using the select cell in a given bag."""
        row = bag.currentRow()
        column = bag.currentColumn()
        item_edit = ItemEdit(self.window, bag.currentItem())

        def update_slot():
            new_slot = item_edit.get_item()
            bag.setItem(row, column, new_slot)

        def trash_slot():
            bag.setItem(row, column, empty_slot())
            item_edit.item_dialog.close()

        item_edit.item_dialog.accepted.connect(update_slot)
        item_edit.item_edit.trash_button.clicked.connect(trash_slot)

    # these are used for connecting the item edit dialog to bag tables
    def new_main_bag_item_edit(self):
        self.new_item_edit(self.ui.main_bag)
    def new_tile_bag_item_edit(self):
        self.new_item_edit(self.ui.tile_bag)
    def new_action_bar_item_edit(self):
        self.new_item_edit(self.ui.action_bar)
    def new_head_item_edit(self):
        self.new_item_edit(self.ui.head)
    def new_chest_item_edit(self):
        self.new_item_edit(self.ui.chest)
    def new_legs_item_edit(self):
        self.new_item_edit(self.ui.legs)
    def new_back_item_edit(self):
        self.new_item_edit(self.ui.back)
    def new_wieldable_item_edit(self):
        self.new_item_edit(self.ui.wieldable)

    def new_blueprint_edit(self):
        # TODO: why does this only work with and instance var but the other
        # ones don't...???
        self.blueprint_lib = BlueprintLib(self.window, self.player.get_blueprints())

        def update_blueprints():
            self.player.set_blueprints(self.blueprint_lib.get_known_list())

        self.blueprint_lib.dialog.accepted.connect(update_blueprints)
        self.blueprint_lib.dialog.show()

    def new_options_dialog(self):
        self.options_dialog = OptionsDialog(self.window)

        def write_options():
            self.options_dialog.write()
            self.ui.statusbar.showMessage("Options have been updated", 3000)

        self.options_dialog.dialog.accepted.connect(write_options)
        self.options_dialog.dialog.show()

    def new_setup_dialog(self):
        self.setup_dialog = OptionsDialog(self.window)

        def write_options():
            self.setup_dialog.write()
            self.setup_dialog.rebuild_db()

        self.setup_dialog.dialog.accepted.connect(write_options)
        # TODO: make sure this is ok to do
        self.setup_dialog.dialog.rejected.connect(sys.exit)
        self.setup_dialog.dialog.exec()

    # these update all values in a stat group at once
    def update_energy(self):
        self.ui.energy.setMaximum(self.ui.max_energy.value())
        self.ui.energy_val.setText(str(self.ui.energy.value()) + " /")
    def update_health(self):
        self.ui.health.setMaximum(self.ui.max_health.value())
        self.ui.health_val.setText(str(self.ui.health.value()) + " /")
    def update_food(self):
        self.ui.food.setMaximum(self.ui.max_food.value())
        self.ui.food_val.setText(str(self.ui.food.value()) + " /")
    def update_warmth(self):
        self.ui.warmth.setMaximum(self.ui.max_warmth.value())
        self.ui.warmth_val.setText(str(self.ui.warmth.value()) + " /")
    def update_breath(self):
        self.ui.breath.setMaximum(self.ui.max_breath.value())
        self.ui.breath_val.setText(str(self.ui.breath.value()) + " /")

    def get_equip(self, name):
        """Return the raw values of both slots in a given equipment bag."""
        equip = getattr(self.ui, name)
        main_cell = equip.item(0, 0)
        glamor_cell = equip.item(0, 1)

        # when you drag itemwidgets around the cell will become empty so just
        # pretend it had an empty slot value
        if main_cell == None or type(main_cell) is QTableWidgetItem:
            main = save_file.empty_slot()
        else:
            main = (main_cell.name, main_cell.item_count, main_cell.variant)

        if glamor_cell == None or type(glamor_cell) is QTableWidgetItem:
            glamor = save_file.empty_slot()
        else:
            glamor = (glamor_cell.name, glamor_cell.item_count, glamor_cell.variant)

        return main, glamor

    def get_bag(self, name):
        """Return the entire contents of a given non-equipment bag as raw values."""
        row = column = 0
        bag = getattr(self.player, "get_" + name)()

        for i in range(len(bag)):
            item = getattr(self.ui, name).item(row, column)
            if type(item) is QTableWidgetItem or item == None:
                item = empty_slot()

            count = item.item_count
            item_type = item.name

            # TODO: variant update support
            # FIXME: this causes a bug where replacing an item with the item
            #        browser will retain the old item's variant data
            #        this kills the item
            variant = bag[i][2]
            bag[i] = (item_type, int(count), variant)

            # so far all non-equip bags are 10 cols long
            column += 1
            if (column % 10) == 0:
                row += 1
                column = 0

        return bag

    def update_bag(self, bag_name):
        """Set the entire contents of any given bag with ItemWidgets based off player data."""
        row = column = 0
        bag = getattr(self.player, "get_" + bag_name)()

        for slot in range(len(bag)):
            widget = ItemWidget(bag[slot])
            getattr(self.ui, bag_name).setItem(row, column, widget)

            column += 1
            if (column % 10) == 0:
                row += 1
                column = 0

    def reload(self):
        """Reload the currently open save file and update GUI values."""
        self.player = save_file.PlayerSave(self.player.filename)
        self.update()
        self.ui.statusbar.showMessage("Reloaded " + self.player.filename, 3000)

    def open_file(self):
        """Display open file dialog and load selected save."""

        character_select = CharacterSelectDialog(self.window)
        character_select.show()
        self.player = character_select.selected

        #filename = QFileDialog.getOpenFileName(self.window,
        #                                       'Open save file...',
        #                                       config.Config().read()["player_folder"],
        #                                       # FIXME: doesn't seem to filter on windows
        #                                       '*.player')
        #
        #try:
        #    self.player = save_file.PlayerSave(filename[0])
        #except FileNotFoundError:
        #    if filename[0] == "":
        #        # they probably clicked cancel
        #        return False
        #    else:
        #        dialog = QMessageBox()
        #        msg = "Could not read file: " + filename[0]
        #        dialog.setText(msg)
        #        dialog.exec()
        #        return False
        #except save_file.WrongSaveVer:
        #    dialog = QMessageBox()
        #    msg = "Save file is not compatible with this version of starcheat."
        #    dialog.setText(msg)
        #    dialog.exec()
        #    return False

        self.update()
        self.window.setWindowTitle("starcheat - " + os.path.basename(self.player.filename))
        self.ui.statusbar.showMessage("Opened " + self.player.filename, 3000)
        return True

if __name__ == '__main__':
    window = MainWindow()
