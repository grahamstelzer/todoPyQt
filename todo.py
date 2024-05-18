import sys
import os
import json
from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFontDatabase
from PyQt5.QtWidgets import QApplication, QMainWindow

projects_dir = 'todoPyQt\projects'

# =======================================================
# TODO: 
# - add draggability
# - make it look better
# =======================================================



qt_creator_file = "mainwindow.ui" # stored in same directory
Ui_MainWindow, QtBaseClass = uic.loadUiType(qt_creator_file) # load
tick = QtGui.QImage('tick.png') # checkmark png

def load_custom_font(font_path):
    font_id = QFontDatabase.addApplicationFont(font_path)
    if font_id == -1:
        print("Failed to load font.")
        return None
    font_family = QFontDatabase.applicationFontFamilies(font_id)
    return font_family[0] if font_family else None


class TodoModel(QtCore.QAbstractListModel):
    def __init__(self, *args, todos=None, **kwargs):
        super(TodoModel, self).__init__(*args, **kwargs) #s inherit from QAbstractListModel (?)
        self.todos = todos or [] # class variable from todos as an arg or create a new empty
        
    # Required methods for QAbstractListModel
    def data(self, index, role):

        # data stored in data.db in the form [status, text] such as [False, "Buy milk"]
        # status changes based on completion

        if role == Qt.DisplayRole:
            _, _, text = self.todos[index.row()] # get text (add ids?)
            return text 
        
        if role == Qt.DecorationRole:
            _, status, _ = self.todos[index.row()] # get status
            if status:
                return tick # return checkmark image

    def rowCount(self, index): # return number of todoss
        return len(self.todos)

    def colCount(self, index):
        return max([indent_level for indent_level, _, _ in self.todos])

    def indent_level(self, index):
        return self.todos[index.row()][0]


# Main window class
class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)

        self.setupUi(self)
        self.model = TodoModel()

        self.load() # load all db files, stores in list

        self.todoView.setModel(self.model)
        self.addButton.pressed.connect(self.add)
        # self.deleteButton.pressed.connect(self.delete)
        # self.completeButton.pressed.connect(self.complete)
        self.nextProjectButton.pressed.connect(self.next_project)
        self.previousProjectButton.pressed.connect(self.previous_project)

        # styling
        # with open('stylesheet.qss', 'r') as f:
        #     self.setStyleSheet(f.read())

        custom_font_path = './fonts/HyperjumpBold.ttf'  # Replace with the path to your custom font file
        custom_font_family = load_custom_font(custom_font_path)
        
        if custom_font_family:
            print(f"Loaded custom font: {custom_font_family}")
            
            # Apply the stylesheet
            with open('stylesheet.qss', 'r') as file:  # Replace with the path to your .qss file
                stylesheet = file.read()
                stylesheet = stylesheet.replace("Arial, sans-serif", f'"{custom_font_family}", sans-serif')
                app.setStyleSheet(stylesheet)

    # key events
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return:
            self.add()
        if event.key() == Qt.Key_Delete:
            self.delete() 
        if event.key() == Qt.Key_Right:
            self.indent(self.todoView.selectedIndexes()[0]) # selected item is index arg
        if event.key() == Qt.Key_Left:
            self.outdent(self.todoView.selectedIndexes()[0])

        modifiers = QtWidgets.QApplication.keyboardModifiers()
        if event.key() == QtCore.Qt.Key_W and modifiers == QtCore.Qt.ControlModifier:
            self.move_up()
            self.todoView.setCurrentIndex(self.todoView.selectedIndexes()[0])
        if event.key() == QtCore.Qt.Key_S and modifiers == QtCore.Qt.ControlModifier:
            self.move_down()
            self.todoView.setCurrentIndex(self.todoView.selectedIndexes()[0])

        if event.key() == QtCore.Qt.Key_C and modifiers == QtCore.Qt.ControlModifier:
            self.complete()

        # press escape to clear currently selected item
        if event.key() == QtCore.Qt.Key_Escape:
                self.todoView.clearSelection()
        

    # add mouse events, draggable entries:
    def mousePressEvent(self, event):
        # since indentation handled via arrow keys, draggability will just change rows:
        pass

    def indent(self, index):
        # this is dumb but we are just going to add 2 spaces to the beginning of text:
        # unpack
        indent_level, _, text = self.model.todos[index.row()]
        # add 4 spaces to the beginning of text:
        text = "    " + text
        # add 1 to indent level
        self.model.todos[index.row()] = (indent_level + 1, _, text)
        self.model.layoutChanged.emit()
        self.save()
    
    def outdent(self, index):
        # remove 4 spaces
        indent_level, _, text = self.model.todos[index.row()]
        text = text[4:]
        if indent_level == 0:
            return
        self.model.todos[index.row()] = (indent_level - 1, _, text)
        self.model.layoutChanged.emit()
        self.save()

    # move items up or down:
    def move_up(self):
        index = self.todoView.selectedIndexes()[0]
        row = index.row()
        if row == 0:
            return
        self.model.todos[row], self.model.todos[row - 1] = self.model.todos[row - 1], self.model.todos[row]
        self.model.layoutChanged.emit()
        self.save()
    def move_down(self):
        index = self.todoView.selectedIndexes()[0]
        row = index.row()
        if row == len(self.model.todos) - 1:
            return
        self.model.todos[row], self.model.todos[row + 1] = self.model.todos[row + 1], self.model.todos[row]
        self.model.layoutChanged.emit()
        self.save()


    def add(self):
        """
        Add an item to our todo list, getting the text from the QLineEdit .todoEdit
        and then clearing it.
        """
        # check if selected topic
        if self.todoView.selectedIndexes():
            print(f"Selected: {self.todoView.selectedIndexes()[0].row()}")
            # get index of selected item
            index = self.todoView.selectedIndexes()[0].row()
            # get text
            text = self.todoEdit.text()
            if text: # Don't add empty strings.
                # Access the list via the model.
                # add item after selected item
                temp = (0, False, "    " + text) # indent function breaks somehow, changing 0 to 1 also breaks
                self.model.todos.insert(index + 1, temp) # inserts into list
                # Trigger refresh.
                self.model.layoutChanged.emit()
                # Empty the input
                self.todoEdit.setText("")
                self.save()
        else:
            # add to end of list
            text = self.todoEdit.text()
            if text:
                self.model.todos.append((0, False, text))
                self.model.layoutChanged.emit()
                self.todoEdit.setText("")
                self.save()

        # text = self.todoEdit.text()
        # if text: # Don't add empty strings.
        #     # Access the list via the model.
        #     self.model.todos.append((0, False, text))
        #     # Trigger refresh.        
        #     self.model.layoutChanged.emit()
        #     # Empty the input
        #     self.todoEdit.setText("")
        #     self.save()
        
    def delete(self):
        indexes = self.todoView.selectedIndexes()
        if indexes:
            # Indexes is a list of a single item in single-select mode.
            index = indexes[0]
            # Remove the item and refresh.
            del self.model.todos[index.row()]
            self.model.layoutChanged.emit()
            # Clear the selection (as it is no longer valid).
            self.todoView.clearSelection()
            self.save()
            
    def complete(self):
        indexes = self.todoView.selectedIndexes()
        if indexes:
            index = indexes[0]
            row = index.row()
            _, status, text = self.model.todos[row]
            self.model.todos[row] = (_, True, text)
         
            # .dataChanged takes top-left and bottom right, which are equal 
            # for a single selection.
            self.model.dataChanged.emit(index, index)
            # Clear the selection (as it is no longer valid).

            self.todoView.clearSelection()
            self.save()
    
    # opening, reading/writing to file:

    def load(self):

        # load in config
        print("Loading config...")
        try:
            if os.path.exists('config.json'):
                with open('config.json', 'r') as config_file:
                    self.config = json.load(config_file)
            else:
                # create default config if it doesn't exist
                pass
        except Exception:
            pass

        # print(self.config)
        self.current_project = self.config.get('current_project')
        # print(self.current_project)
        # update titleLabel
        self.titleLabel.setText(self.current_project)

        print("Loading projects...")
        try:
            files = os.listdir('./projects')
            self.files = files
            # print(files)
            # setup index for current project
            if self.current_project:
                self.current_project_index = files.index(self.current_project)
                # print(self.current_project_index)
            else:
                self.current_project_index = 0
        except Exception:
            pass
        print(f"Successfulyy loaded {len(self.files)} projects...")
        # load project
        self.load_project(self.current_project_index)

    def load_project(self, project_index):
        # load project
        print(f"Attempting to load project {self.files[project_index]}...")
        try:
            with open(f'projects/{self.files[project_index]}', 'r') as f:
                data = json.load(f)
        except json.JSONDecodeError:
            data = []

        print(f"Successfully loaded project {self.files[project_index]}...")
        self.model.todos = data
        self.model.layoutChanged.emit()
        self.titleLabel.setText(self.current_project)

    def next_project(self):
        self.save()
        self.current_project_index += 1
        if self.current_project_index >= len(self.files):
            self.current_project_index = 0
        self.current_project = self.files[self.current_project_index]
        self.load_project(self.current_project_index)


    def previous_project(self):
        self.save()
        self.current_project_index -= 1
        if self.current_project_index < 0:
            self.current_project_index = len(self.files) - 1
        self.current_project = self.files[self.current_project_index]
        self.load_project(self.current_project_index)   

    
    def save(self):
        print(f"Saving project {self.files[self.current_project_index]}...")
        with open(f'projects/{self.files[self.current_project_index]}', 'w') as f:
            data = json.dump(self.model.todos, f)
        # update config.json:
        # print("Saving config...")
        try:    
            with open('config.json', 'w') as config_file:
                self.config['current_project'] = self.current_project
                json.dump(self.config, config_file)
        except Exception as e:
            print(f"Error saving config: {e}")


app = QtWidgets.QApplication(sys.argv)
window = MainWindow() 
window.show()
app.exec_()


