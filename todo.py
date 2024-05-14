import sys
import json
from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtCore import Qt


# =======================================================
# TODO: 
# - add draggability
# - make it look better
# =======================================================



qt_creator_file = "mainwindow.ui" # stored in same directory
Ui_MainWindow, QtBaseClass = uic.loadUiType(qt_creator_file) # load
tick = QtGui.QImage('tick.png') # checkmark png


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
        self.load()
        self.todoView.setModel(self.model)
        self.addButton.pressed.connect(self.add)
        # self.deleteButton.pressed.connect(self.delete)
        # self.completeButton.pressed.connect(self.complete)

        # styling
        with open('stylesheet.qss', 'r') as f:
            self.setStyleSheet(f.read())

    # key events
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return:
            self.add()
        if event.key() == Qt.Key_Delete:
            self.delete() 
        # if event.key() == Qt.Key_Space: # doesnt work, maybe need to select item?
        #     self.complete()
        if event.key() == Qt.Key_Right:
            self.indent(self.todoView.selectedIndexes()[0]) # selected item is index arg
        if event.key() == Qt.Key_Left:
            self.outdent(self.todoView.selectedIndexes()[0])

        modifiers = QtWidgets.QApplication.keyboardModifiers()
        if event.key() == QtCore.Qt.Key_W and modifiers == QtCore.Qt.ControlModifier:
            self.move_up()
        if event.key() == QtCore.Qt.Key_S and modifiers == QtCore.Qt.ControlModifier:
            self.move_down()



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
        text = self.todoEdit.text()
        if text: # Don't add empty strings.
            # Access the list via the model.
            self.model.todos.append((0, False, text))
            # Trigger refresh.        
            self.model.layoutChanged.emit()
            # Empty the input
            self.todoEdit.setText("")
            self.save()
        
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
        try:
            with open('data.db', 'r') as f:
                self.model.todos = json.load(f)
        except Exception:
            pass

    
    def save(self):
        with open('data.db', 'w') as f:
            data = json.dump(self.model.todos, f)


app = QtWidgets.QApplication(sys.argv)
window = MainWindow() 
window.show()
app.exec_()


