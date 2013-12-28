"""
Module for reading and indexing Starbound assets
"""

import os, json, re, sqlite3
from platform import system

from config import config

# Regular expression for comments
comment_re = re.compile(
    '(^)?[^\S\n]*/(?:\*(.*?)\*/[^\S\n]*|/[^\n]*)($)?',
    re.DOTALL | re.MULTILINE
)

# source: http://www.lifl.fr/~riquetd/parse-a-json-file-with-comments.html
def parse_json(filename):
    """ Parse a JSON file
        First remove comments and then use the json module package
        Comments look like :
            // ...
        or
            /*
            ...
            */
    """
    with open(filename) as f:
        content = ''.join(f.readlines())

        # Looking for comments
        match = comment_re.search(content)
        while match:
            # single line comment
            content = content[:match.start()] + content[match.end():]
            match = comment_re.search(content)

        # Return json file
        return json.loads(content)

class AssetsDb():
    def __init__(self):
        try:
            open(config["assets_db"])
        except FileNotFoundError:
            self.init_db()

        self.db = sqlite3.connect(config["assets_db"])

    def init_db(self):
        tables = ("create table items (name text, filename text, folder text, icon text, category text)",
                  "create table blueprints (name text, filename text, folder text, category text)")
        db = sqlite3.connect(config["assets_db"])
        c = db.cursor()

        for q in tables:
            c.execute(q)
        db.commit()
        db.close()

        Items().add_all_items()
        Blueprints().add_all_blueprints()

class Blueprints():
    def __init__(self):
        self.blueprints_folder = os.path.join(config["assets_folder"], "recipes")
        self.db = AssetsDb().db

    def file_index(self):
        index = []
        for root, dirs, files in os.walk(self.blueprints_folder):
            for f in files:
                if re.match(".*\.recipe", f) != None:
                    index.append((f, root))
        print("Found " + str(len(index)) + " blueprint files")
        return index

    def add_all_blueprints(self):
        index = self.file_index()
        blueprints = []
        print("Indexing", end="")
        for f in index:
            full_path = os.path.join(f[1], f[0])

            try:
                info = parse_json(full_path)
            except ValueError:
                continue

            name = f[0].partition(".")[0]
            filename = f[0]
            folder = f[1]

            try:
                category = info["groups"][1]
            except (KeyError, IndexError):
                category = "other"

            blueprints.append((name, filename, folder, category))
            print(".", end="")
        c = self.db.cursor()
        q = "insert into blueprints values (?, ?, ?, ?)"
        c.executemany(q, blueprints)
        self.db.commit()
        print("Done!")

    def get_all_blueprints(self):
        c = self.db.cursor()
        c.execute("select * from blueprints order by name collate nocase")
        return c.fetchall()

    def get_categories(self):
        c = self.db.cursor()
        c.execute("select distinct category from blueprints order by category")
        return c.fetchall()

    def filter_blueprints(self, category, name):
        if category == "<all>":
            category = "%"
        name = "%" + name + "%"
        c = self.db.cursor()
        q = "select * from blueprints where category like ? and name like ? order by name collate nocase"
        c.execute(q, (category, name))
        result = c.fetchall()
        return result

class Items():
    def __init__(self):
        self.items_folder = os.path.join(config["assets_folder"], "items")
        self.objects_folder = os.path.join(config["assets_folder"], "objects")
        self.tech_folder = os.path.join(config["assets_folder"], "tech")
        self.ignore_items = ".*\.(png|config|frames|coinitem)"
        self.db = AssetsDb().db

    def file_index(self):
        index = []
        # regular items
        for root, dirs, files in os.walk(self.items_folder):
            for f in files:
                # don't care about png and config and all that
                if re.match(self.ignore_items, f) == None:
                    index.append((f, root))
        # objects
        for root, dirs, files in os.walk(self.objects_folder):
            for f in files:
                if re.match(".*\.object$", f) != None:
                    index.append((f, root))
        # techs
        for root, dirs, files in os.walk(self.tech_folder):
            for f in files:
                if re.match(".*\.techitem$", f) != None:
                    index.append((f, root))
        print("Found " + str(len(index)) + " item files")
        return index

    def add_all_items(self):
        index = self.file_index()
        items = []
        print("Indexing", end="")
        for f in index:
            full_path = os.path.join(f[1], f[0])
            try:
                info = parse_json(full_path)
            except ValueError:
                continue

            try:
                name = info["itemName"]
            except KeyError:
                try:
                    name = info["name"]
                except KeyError:
                    name = info["objectName"]

            filename = f[0]
            path = f[1]
            category = f[0].partition(".")[2]

            try:
                asset_icon = info["inventoryIcon"]
                if re.match(".*\.techitem$", f[0]) != None:
                    icon = config["assets_folder"] + asset_icon
                    # index dynamic tech chip items too
                    # TODO: do we keep the non-chip items in or not? i don't
                    #       think you're meant to have them outside tech slots
                    chip_name = name + "-chip"
                    items.append((chip_name, filename, path, icon, category))
                else:
                    icon = os.path.join(f[1], info["inventoryIcon"])
            except KeyError:
                # TODO: still working these out. check out crafted weaps too
                if re.search("(sword|shield)", category) != None:
                    cat = category.replace("generated", "")
                    icon = os.path.join(config["assets_folder"], "interface", "inventory", cat + ".png")
                else:
                    icon = os.path.join(config["assets_folder"], "interface", "inventory", "x.png")

            items.append((name, filename, path, icon, category))
            print(".", end="")

        c = self.db.cursor()
        q = "insert into items values (?, ?, ?, ?, ?)"
        c.executemany(q, items)
        self.db.commit()
        print("Done!")

    def get_all_items(self):
        c = self.db.cursor()
        c.execute("select * from items order by name collate nocase")
        return c.fetchall()

    def get_item(self, name):
        c = self.db.cursor()
        c.execute("select folder, filename from items where name = ?", (name,))
        meta = c.fetchone()
        item = parse_json(os.path.join(meta[0], meta[1]))
        return item, meta[0], meta[1]

    def get_categories(self):
        c = self.db.cursor()
        c.execute("select distinct category from items order by category")
        return c.fetchall()

    def get_item_icon(self, name):
        c = self.db.cursor()
        c.execute("select icon from items where name = ?", (name,))
        try:
            icon_file = c.fetchone()[0]
            # TODO: just double check the split usage, may be deprecated
            if system() != 'Windows':
                icon = icon_file.split(':')
            else:
                icon = icon_file.rsplit(':', icon_file.count(':') - 1)
            if len(icon) < 2:
                icon = icon[0], 0
        except TypeError:
            return None

        try:
            open(icon[0])
        except FileNotFoundError:
            return None

        if icon[1] == "chest":
            return icon[0], 16
        elif icon[1] == "pants":
            return icon[0], 32

        return icon[0], 0

    # TODO: this is not written yet
    def get_item_image(self, item):
        """Return a vaild item image from item options."""
        # TODO: support for frame selectors
        if "image" in item:
            if re.search(":", item["image"]):
                image = item["image"].partition(":")[0]
        try:
            icon_file = item["image"]
        except KeyError:
            pass

    def missing_icon(self):
        return os.path.join(config["assets_folder"], "interface", "inventory", "x.png")

    def filter_items(self, category, name):
        if category == "<all>":
            category = "%"
        name = "%" + name + "%"
        c = self.db.cursor()
        c.execute("select * from items where category like ? and name like ? order by name collate nocase",
                  (category, name))
        result = c.fetchall()
        return result
