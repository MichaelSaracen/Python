import sys

from PySide6.QtWidgets import QApplication, QWidget, QHBoxLayout
from StatChart import StatChart

if __name__ == '__main__':
    app: QApplication = QApplication(sys.argv)

    w: QWidget = QWidget()
    layout: QHBoxLayout = QHBoxLayout(w)

    statChart: StatChart = StatChart(w)
    statChart.show()
    statChart.setHeaders(["strength", "agility", "dexterity", "vitality", "intelligence"])
    statChart.setValues([0.7, 0.55, 0.6, 1, 0.9])
    statChart.setAnimationEnabled(True)
    statChart.setRotation(30)

    layout.addWidget(statChart)

    w.show()
    app.exec()