# Author: Yunkun Liao
# Define outlog for GUI
# reference from https://www.cnblogs.com/Garfield

from PyQt5.QtGui import QTextCursor

class OutLog:
    def __init__(self, edit, out=None, color=None):
        """(edit, out=None, color=None) -> can write stdout, stderr to a
        QTextEdit.
        edit = QTextEdit
        out = alternate stream ( can be the original sys.stdout )
        color = alternate color (i.e. color stderr a different color)
        """

        self.edit = edit
        self.out = None
        self.color = color

    def write(self, m):
        global aSignalOutLog
        
        if self.color:
            tc = self.edit.textColor()
            self.edit.setTextColor(self.color)

        self.edit.moveCursor(QTextCursor.End)
        self.edit.insertPlainText(m)

        if self.color:
            self.edit.setTextColor(tc)

        if self.out:
            self.out.write(m)
