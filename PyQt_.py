import sys
import h5py
import numpy as np
from scipy import special, constants
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QApplication, QMainWindow, QItemDelegate, QInputDialog, QFileDialog
from PyQt5.QtCore import Qt, QAbstractTableModel
from PyQt5.QtGui import QBrush
import pyqtgraph as pg

class ComboBoxDelegate(QItemDelegate):
    def __init__(self):
        super().__init__()

    def createEditor(self, parent, option, index):
        '''Устанавливается редактор(выпадающий список) в 1 столбец со значениями от 0 до 5'''
        if (index.column()==0):
            editor = QtWidgets.QComboBox(parent)
            editor.addItems([str(i) for i in range(0, 6)])
            return editor
        else:
            return super().createEditor(parent, option, index)

    def setEditorData(self, editor, index):
        '''Заполняем начальным значением редактор'''
        if (index.column()==0):
            value = index.model().data(index, Qt.DisplayRole)
            editor.setCurrentText(value)
        else:
            super().setEditorData(editor, index)

    def setModelData(self, editor, model, index):
        '''Передаем выбранное значение редактора модели'''
        if (index.column() == 0):
            value = editor.currentText()
            model.setData(index, value, Qt.EditRole)
        else:
            super().setModelData(editor, model, index)

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)

class TableModel(QAbstractTableModel):

    def __init__(self):
        '''Изначально будет создаваться модель(матрица), заполненная нулями  '''
        super().__init__()
        self.arr = np.zeros((7, 5), dtype='f')

    def rowCount(self, index):
        return self.arr.shape[0]

    def columnCount(self, index):
        return self.arr.shape[1]

    def data(self, index, role=Qt.DisplayRole):
        '''Отображаем данные в таблице'''
        if role == Qt.DisplayRole:
            if index.column() == 0:
                return f"{self.arr[index.row(), index.column()]:.0f}"
            return str(self.arr[index.row(), index.column()])
        elif role == Qt.TextAlignmentRole:
            return Qt.AlignCenter
        elif role == Qt.BackgroundRole and index.column() == 2: #в 3 столбце таблице ячейки будут заливаться в зависимости от значений
            return QBrush(self.calculateColor(index.row()))
        return None

    def setData(self, index, value, role=Qt.EditRole):
        '''Устанавливаем значение в модели'''
        if role == Qt.EditRole and value:
            self.arr[index.row(), index.column()] = float(value)
            self.dataChanged.emit(index, index)
            if index.column() == 0: #2 и 3 столбцы будут зависеть от 1 столбца в таблице
                self.updateSecondColoumn(index.row())
                self.updateThirdColoumn(index.row())
            return True
        return False

    def flags(self, index):
        '''Редактировать нельзя 2 и 3 столбцы в таблице'''
        col = index.column()
        if col == 1 or col == 2:
             return Qt.ItemIsSelectable | Qt.ItemIsEnabled
        else:
             return Qt.ItemIsEditable | Qt.ItemIsSelectable | Qt.ItemIsEnabled

    def updateSecondColoumn(self, row):
        '''По формуле обновляем значение во 2 столбце'''
        col_1 = self.arr[row, 0]
        col_2 = (special.sindg(col_1 * 17) - special.cosdg(col_1 * 17)) * constants.pi
        self.arr[row, 1] = col_2
        index = self.index(row, 1)
        self.dataChanged.emit(index, index)

    def updateThirdColoumn(self, row):
        '''3 столбец будет содержать накопленные значение из 2 столбца'''
        self.arr[row, 2] = self.arr[row, 2] + self.arr[row, 1]
        index = self.index(row, 2)
        self.dataChanged.emit(index, index)

    def resize(self, rows, cols):
        '''Меняем структуру модели'''
        current_rows = self.arr.shape[0]
        current_cols = self.arr.shape[1]

        if current_rows == rows and current_cols == cols: #Если текущий размер массива совпадает с новым размером, то не меняем
            return

        if current_rows > rows: #Если текущее кол-во строк больше нового кол-ва строк, то удаляем лишние строки
            self.arr = np.delete(self.arr, np.s_[rows:], axis=0)
        elif current_rows < rows: #Если текущее кол-во строк меньше нового кол-ва строк, то добавляем новые строки с нулями
            new_arr = np.zeros((rows - current_rows, current_cols))
            self.arr = np.concatenate((self.arr, new_arr), axis=0)

        if current_cols > cols:  # Если текущее кол-во cтолбцов больше нового кол-ва столбцов, то удаляем лишние столбцы
            self.arr = np.delete(self.arr, np.s_[cols:], axis=1)
        elif current_cols < cols:  # Если текущее кол-во cтолбцов меньше нового кол-ва столбцов, то добавляем новые столбцы с нулями
            new_arr = np.zeros((rows, cols - current_cols))
            self.arr = np.concatenate((self.arr, new_arr), axis=1)

        self.layoutChanged.emit()

    def random(self):
        '''Заполняем модель случайными значениями'''
        rows = self.arr.shape[0]
        cols = self.arr.shape[1]
        if rows > 0:
            #Если существует первый столбец, то заполняем его значениями от 0 до 5, как из выпадающего списка
            if cols > 0:
                self.arr[:, 0] = np.round(5 * np.random.random((rows, )))
                index_1 = self.index(0, 0)
                index_2 = self.index(rows, 0)
                self.dataChanged.emit(index_1, index_2)
            #Если существует второй столбец, то обновляем его
            if cols > 1:
                updateSecondCol = np.vectorize(self.updateSecondColoumn, otypes=[float])
                updateSecondCol(np.arange(rows))
            #Если существует третий столбец, то обновляем его
            if cols > 2:
                updateThirdCol = np.vectorize(self.updateThirdColoumn, otypes=[float])
                updateThirdCol(np.arange(rows))
            #Если существуют ещё столбцы, то заполняем их случайными значениями от -10 до 10
            if cols > 3:
                new_arr = 20 * np.random.random((rows, cols - 3)) - 10
                self.arr[:, 3:] = new_arr
                index_1 = self.index(0, 3)
                index_2 = self.index(rows, cols)
                self.dataChanged.emit(index_1, index_2)

    def calculateColor(self, row):
        '''Вычисляем цвет для ячейки 3 столбца'''
        if self.arr[row, 3] > 0:
            return Qt.green
        elif self.arr[row, 3] < 0:
            return Qt.red
        return Qt.white

    def reset(self):
        '''Модель приводим к исходному состоянию'''
        new_arr = np.zeros((7, 5), dtype = 'f')
        self.arr = new_arr
        self.layoutChanged.emit()

    def load(self, data):
        self.arr = data
        self.layoutChanged.emit()

    def getCols(self, selectCol):
        '''Передаем отмеченные столбцы для постройки графика'''
        col_1 = selectCol[0]
        col_2 = selectCol[1]
        coloumns = np.array([self.arr[:, col_1], self.arr[:, col_2]])
        return coloumns
class Window(QMainWindow):

    def __init__(self):
        super(Window, self).__init__()
        self.setWindowTitle("Table_Graph")
        self.setGeometry(400, 150, 550, 800)

        self.layoutVB = QtWidgets.QVBoxLayout()
        self.main_widget = QtWidgets.QWidget()
        self.main_widget.setLayout(self.layoutVB)
        self.setCentralWidget(self.main_widget)

        self.tableView = QtWidgets.QTableView()
        self.layoutVB.addWidget(self.tableView)

        self.tableModel = TableModel()
        self.comboBoxDel = ComboBoxDelegate()
        self.tableView.setModel(self.tableModel)
        self.tableView.setItemDelegate(self.comboBoxDel)

        self.plot = pg.PlotWidget()
        self.layoutVB.addWidget(self.plot)

        self.btn_plot = QtWidgets.QPushButton()
        self.layoutVB.addWidget(self.btn_plot)
        self.btn_plot.setText("Построить график")

        self.btn_resize = QtWidgets.QPushButton()
        self.layoutVB.addWidget(self.btn_resize)
        self.btn_resize.setText("Изменить размер таблицы")

        self.btn_random = QtWidgets.QPushButton()
        self.layoutVB.addWidget(self.btn_random)
        self.btn_random.setText("Заполнить случайными числами")

        self.btn_save = QtWidgets.QPushButton()
        self.layoutVB.addWidget(self.btn_save)
        self.btn_save.setText("Сохранить в hdf")

        self.btn_load = QtWidgets.QPushButton()
        self.layoutVB.addWidget(self.btn_load)
        self.btn_load.setText("Загрузить из hdf")

        self.btn_reset = QtWidgets.QPushButton()
        self.layoutVB.addWidget(self.btn_reset)
        self.btn_reset.setText("Сброс")

        self.add_func()

    def add_func(self):
        self.btn_plot.clicked.connect(self.plotGraph)
        self.btn_resize.clicked.connect(self.resizeArray)
        self.btn_random.clicked.connect(self.fillRandom)
        self.btn_load.clicked.connect(self.loadFile)
        self.btn_save.clicked.connect(self.saveFile)
        self.btn_reset.clicked.connect(self.resetTable)

    def plotGraph(self):
        '''Находим индексы веделенных столбцов'''
        selectColumns = []
        selectModel = self.tableView.selectionModel()
        if selectModel.hasSelection():
            selectedIndexes = selectModel.selection().indexes()
            for index in selectedIndexes:
                column = index.column()
                if column not in selectColumns:
                    selectColumns.append(column)
        '''Строим по ним график при условии, что столбцов было веделено ровно 2'''
        if len(selectColumns) == 2:
            coloumns = self.tableModel.getCols(selectColumns)
            self.plot.clear()
            self.plot.plot(coloumns[0], coloumns[1], pen = 'red')

    def resizeArray(self):
        """Функция для изменения размера массива по клику кнопки"""
        # Получение нового размера массива от пользователя
        rows, ok1 = QInputDialog.getInt(self, "Изменение размера", "Введите новое количество строк:")
        cols, ok2 = QInputDialog.getInt(self, "Изменение размера", "Введите новое количество столбцов:")

        # Если пользователь нажал "ОК" в обоих диалоговых окнах
        if ok1 and ok2:
            # Изменение размера модели данных
            self.tableModel.resize(rows, cols)

    def fillRandom(self):
        self.tableModel.random()

    def resetTable(self):
        self.tableModel.reset()

    def loadFile(self):
        f_path = QFileDialog.getOpenFileName(self, "Выберите файл", "", "HDF5 Files (*.h5)")[0]
        if f_path:
            try:
                with h5py.File(f_path, 'r') as file:
                    data = file['matrix'][:]
                    self.tableModel.load(data)
            except FileNotFoundError:
                pass

    def saveFile(self):
        f_path = QFileDialog.getSaveFileName(self, "Выберите файл", "", "HDF5 Files (*.h5)")[0]
        if f_path:
            try:
                with h5py.File(f_path, 'w') as file:
                    file.create_dataset('matrix', data=self.tableModel.arr, dtype='f')
            except FileNotFoundError:
                pass


def application():
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    application()

