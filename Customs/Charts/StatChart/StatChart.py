__version__ = "1.0.0"
__author__ = "Michael Saracen"
__status__ = "None"
__date__ = "06.06.2025"

import math
import random
from typing import List

from PySide6.QtCore import QRect, QPoint, QPointF, QPropertyAnimation, Signal, Property, QAbstractAnimation, \
    QPauseAnimation, QSequentialAnimationGroup, QTimer, QEasingCurve
from PySide6.QtGui import QPainter, QPainterPath, QGradient, QPen, QColor, Qt, QFontMetrics
from PySide6.QtWidgets import QWidget, QGraphicsDropShadowEffect


class StatChart(QWidget):
    """
    Die Klasse StatChart ist ein benutzerdefiniertes PySide6-Widget zur Visualisierung von statistischen Werten
    in Form eines rotierenden, radarbasierten Diagramms (auch bekannt als Spinnennetzdiagramm oder Radar Chart).

    Hauptfunktionen:
    - Darstellung von mehreren Werten entlang radialer Achsen, wobei jeder Wert durch eine Linie dargestellt wird.
    - Unterstützung für Animation: Das Diagramm kann sich automatisch im Kreis drehen, wobei die Geschwindigkeit
      und Pausenzeit anpassbar sind.
    - Visuelle Anpassbarkeit: Hintergrundfarbe oder -verlauf, Farben für Text und Formen können individuell gesetzt
      werden.
    - Dynamisches Zeichnen der Header (Achsenbeschriftungen) und Prozentwerte entlang der Linien.
    - Unterstützung für Schatteneffekte zur optischen Aufwertung.

    Anforderungen:
    - Mindestens vier Header (Achsenbeschriftungen) mit jeweils mindestens zwei Zeichen.
    - Die Anzahl der Werte muss mit der Anzahl der Header übereinstimmen und mindestens vier betragen.
    - Alle Werte müssen Gleitkommazahlen (float) zwischen 0.0 und 1.0 sein, wobei sie den relativen Fortschritt je
      Achse darstellen.

    Eigenschaften:
    - backgroundColor (QColor): Hintergrundfarbe der zentralen Ellipse.
    - backgroundGradient (QGradient): Alternativer Farbverlauf als Hintergrund.
    - shapeColor (QColor): Farbe des Pfades, der die Werte verbindet.
    - textColor (QColor): Farbe der Beschriftungstexte.
    - rotation (int): Aktueller Rotationswinkel des Diagramms.
    - headers (List[str]): Liste der Achsentitel.
    - values (List[float]): Liste der Werte für die Darstellung.

    Verwendung:
    Die Klasse eignet sich ideal zur Darstellung von KPIs, Leistungsmetriken, Spielerstatistiken oder beliebigen
    Mehrfachwerten in einer vergleichenden, radialen Anordnung.

    Beispiel:
        chart = StatChart()
        chart.setHeaders(["Stärke", "Geschick", "Intelligenz", "Ausdauer"])
        chart.setValues([0.8, 0.6, 0.9, 0.7])
        chart.setBackgroundColor(QColor("white"))
        chart.setShapeColor(QColor("blue"))
        chart.setTextColor(QColor("black"))
    """

    # Annotations
    _animation_enabled: bool
    _background_color: QColor
    _background_gradient: QGradient|None
    _headers: List[str]
    _pause_animation: QPauseAnimation
    _rotation: int
    _rotation_animation: QPropertyAnimation
    _sequential_animation: QSequentialAnimationGroup
    _shape_color: QColor
    _text_color: QColor
    _value_count: int
    _values: List[float]

    # Signals
    backgroundColorChanged: Signal = Signal(QColor)
    backgroundGradientChanged: Signal = Signal(QGradient)
    headersChanged: Signal = Signal(list)
    rotationChanged: Signal = Signal(int)
    shapeColorChanged: Signal = Signal(QColor)
    textColorChanged: Signal = Signal(QColor)
    valuesChanged: Signal = Signal(list)

    def __init__(self, parent: QWidget = None):
        super().__init__(parent=parent)
        self._animation_enabled = True
        self._background_color = QColor()
        self._background_gradient = QGradient(QGradient.Preset.SaintPetersburg)

        self._headers = []
        self._rotation = 0
        self._shape_color = QColor(12, 170, 255, 100)
        self._text_color = QColor(0, 0, 0, 180)
        self._value_count = 0
        self._values = []

        self.setContentsMargins(50, 50, 50, 50)
        self.setMinimumSize(500, 500)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground)

        if parent:
            shadow: QGraphicsDropShadowEffect = QGraphicsDropShadowEffect(
                self,
                offset=QPointF(0,0),
                blurRadius=20,
                color=QColor(0,0,0,55)
            )
            self.setGraphicsEffect(shadow)

        if self._animation_enabled:
            self._rotation_animation = QPropertyAnimation(self, b"rotation")
            self._rotation_animation.setDuration(750)
            self._rotation_animation.setEasingCurve(QEasingCurve.Type.InOutBack)

            self._pause_animation = QPauseAnimation(self, duration=1000)

            self._sequential_animation = QSequentialAnimationGroup()
            self._sequential_animation.addAnimation(self._rotation_animation)
            self._sequential_animation.addAnimation(self._pause_animation)
            self._sequential_animation.finished.connect(self._startRotationLoop)

    # ▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬ Getter & Setter
    def backgroundColor(self) -> QColor:
        """
        Gibt die Hintergrundfarbe des Widgets wieder.
        :return: QColor
        """
        return self._background_color

    def backgroundGradient(self) -> QGradient:
        """
        Gibt den Hintergrundgradienten des Widgets wieder.
        :return: QGradient
        """
        return self._background_gradient

    def header(self) -> List[str]:
        """
        Gibt eine Liste mit den gesetzten Headern wieder.
        :return: List[str]
        """
        return self._headers

    def rotation(self) -> int:
        """
        Gibt die aktuelle Rotation des Widgets wieder.
        :return:
        """
        return self._rotation

    def setAnimationEnabled(self, enabled: bool) -> None:
        """
        Setzen des States der Sequential-Animation.
        Der State der Animation ist per Defaultwert True, das heißt, dass diese direkt ausgeführt wird.
        Um dies auszuschalten, muss 'setAnimationEnabled' auf False gesetzt werden.
        :param enabled:
        """
        if enabled:
            if self._sequential_animation.state() == QAbstractAnimation.State.Running:
                return
            QTimer.singleShot(1000, self._startRotationLoop)
        else:
            self._sequential_animation.stop()
        self._animation_enabled = enabled

    def setAnimationRotationSpeed(self, speed: int) -> None:
        """
        Setzt die Geschwindigkeit, mit der sich das Widget bei der Animation bewegt.
        Defaultwert ist 750.
        Kleinster wert ist 200. Alles darunter wird ignoriert und automatisch auf 200 gesetzt.
        :param speed:
        """
        self._rotation_animation.setDuration(max(speed, 200))

    def setAnimationPauseDuration(self, duration):
        """
        Die Zeit, wie lange die Animation pausieren soll. Minimum sind 250 ms.
        :param duration:
        """
        self._pause_animation.setDuration(max(duration, 250))

    def setBackgroundColor(self, color: QColor) -> None:
        """
        Setzt die Hintergrundfarbe (Ellipse).
        :param color:
        """
        self._background_gradient = None
        self._background_color = color
        self.backgroundColorChanged.emit(color)

    def setBackgroundGradient(self, gradient: QGradient) -> None:
        """
        Setzt den Hintergrundgradienten.
        Setzt den Backgroundcolor zurück.
        :param gradient:
        :return:
        """
        self._background_color = QColor()
        self._background_gradient = gradient
        self.backgroundGradientChanged.emit(gradient)

    def setRotation(self, rotation: int) -> None:
        """
        Setzt die Rotation für das Widget.
        Defaultwert ist 0
        :param rotation:
        :return:
        """
        self._rotation = rotation % 360
        self.rotationChanged.emit(self._rotation)
        self.update()
        # print(self._rotation)

    def setHeaders(self, headers: List[str]) -> None:
        """
        Setzen der Header.
        Es müssen mindestens vier Header gesetzt werden (als Zeichenkette), ansonsten wird
        ein ValueError geworfen.
        Ein Header muss mindestens zwei Charaktere enthalten.
        :param headers:
        :return:
        """
        self.__validate_headers(headers)
        if self._headers != headers:
            self._headers = headers
            self.headersChanged.emit(headers)

    def setShapeColor(self, color: QColor) -> None:
        """
        Setzt die Farbe für die Anzeige der Fortschritte.
        :param color:
        """
        if self._shape_color != color:
            self._shape_color = color
            self.shapeColorChanged.emit(color)

    def setTextColor(self, color: QColor) -> None:
        """
        Setzt die Farbe für die Header und für die Values.
        :param color:
        """
        if self._text_color != color:
            self._text_color = color
            self.textColorChanged.emit(color)

    def setValues(self, values: List[float]) -> None:
        """
        Festlegen der Werte mit einer Liste und Fließkommazahlen.
        :param values:
        :return:
        """
        self.__validate_values(values)
        if self._values != values:
            self._values = values
            self._value_count = len(self._values)
            self.valuesChanged.emit(values)

    def shapeColor(self) -> QColor:
        """
        Gibt die Farbe des Fortschrittes wieder.
        :return:
        """
        return self._shape_color

    def textColor(self) -> QColor:
        """
        Gibt die Farbe der Header und Values wieder.
        :return:
        """
        return self._text_color

    def values(self) -> List[float]:
        """
        Gibt alle Values wieder, die sich in der Liste 'values' befinden.
        :return:
        """
        return self._values

    # ▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬ Properties
    backgroundColor = Property(QColor, fget=backgroundColor, fset=setBackgroundColor, notify=backgroundColorChanged)
    backgroundGradient = Property(
        QGradient,
        fget=backgroundGradient,
        fset=setBackgroundGradient,
        notify=backgroundGradientChanged
    )
    headers = Property(list, fget=header, fset=setHeaders, notify=headersChanged)
    rotation = Property(int, fget=rotation, fset=setRotation, notify=rotationChanged)
    shapeColor = Property(QColor, fget=shapeColor, fset=setShapeColor, notify=shapeColorChanged)
    textColor = Property(QColor, fget=textColor, fset=setTextColor, notify=textColorChanged)
    values = Property(list, fget=values, fset=values, notify=valuesChanged)

    # ▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬ Paint Event
    def paintEvent(self, event, /):
        self.__validate_headers_values(self._headers, self._values)

        painter: QPainter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        base_rect = self.__baseRect()

        painter.save()
        painter.translate(base_rect.center())
        painter.rotate(self._rotation)

        # ==================================================================================== Ellipse
        ellipse_rect: QRect = QRect(-base_rect.width() // 2, -base_rect.height() // 2,
                                    base_rect.width(), base_rect.height())

        painter.setPen(QPen(QColor(0, 0, 0, 30), 1, Qt.PenStyle.SolidLine))
        if self._background_color.isValid():
            painter.setBrush(self._background_color)
        else:
            painter.setBrush(self._background_gradient)
        outer_ellipse: QPainterPath = QPainterPath()
        outer_ellipse.addEllipse(ellipse_rect)
        painter.drawPath(outer_ellipse)

        # ==================================================================================== Orientierungslinien
        painter.setPen(QPen(QColor(0,0,0, 40), 1, Qt.PenStyle.DashLine))
        orientation_lines: List[QPainterPath] = self.__orientationLines(painter, outer_ellipse)

        self.__drawHeader(painter, orientation_lines)

        painter.setPen(QPen(QColor(0, 0, 0, 100), 1, Qt.PenStyle.SolidLine))
        # Pfad für Werte
        path: QPainterPath = QPainterPath()
        # Startpos
        first_index: int = 0
        first_pos: QPointF = orientation_lines[first_index].pointAtPercent(self._values[first_index])
        path.moveTo(first_pos)

        for i in range(1, len(orientation_lines)):
            pos: QPointF = orientation_lines[i].pointAtPercent(self._values[i])
            path.lineTo(pos)

        path.closeSubpath()


        painter.drawPath(path)

        painter.restore()

    # ▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬ Helpers
    def _startRotationLoop(self) -> None:
        """
        Animations-Helfer.
        :return:
        """
        if self._value_count == 0:
            return

        # Schritte mit dem sich das Widget bewegen soll
        step = 360 // self._value_count

        # End-Value für die Rotation Animation
        next_rotation = self._rotation + step

        # Pausenzeiten Random würfeln
        rnd_pause: int = random.randint(self._pause_animation.duration(), 3000)
        self._pause_animation.setDuration(rnd_pause)

        self._rotation_animation.setStartValue(self._rotation)
        self._rotation_animation.setEndValue(next_rotation)
        self._sequential_animation.start()

    def __baseRect(self) -> QRect:
        """
        Base rect welche die Ellipse mittig im Widget platziert.
        :return:
        """
        size: int = min(self.width(), self.height())
        base_rect: QRect = QRect(0, 0, size, size).marginsRemoved(self.contentsMargins())
        base_rect.moveCenter(QPoint(self.rect().center().x(), self.rect().center().y()))
        return base_rect

    def __drawHeader(self, painter: QPainter, orientation_lines):
        """
        Zeichnen der Header die sich im Widget befinden, und diese Parallel zu den Linien ausrichten.
        :param painter:
        :param orientation_lines:
        :return:
        """
        painter.setBrush(self._shape_color)

        for i in range(len(orientation_lines)):
            line = orientation_lines[i]

            painter.save()
            painter.translate(line.pointAtPercent(1))
            painter.rotate(math.degrees(math.atan2(line.pointAtPercent(0.95).y(), line.pointAtPercent(0.95).x())))

            painter.setPen(QPen(self._text_color))
            metrics: QFontMetrics = QFontMetrics(painter.font())
            w = metrics.horizontalAdvance(self._headers[i])
            painter.drawText(QPointF(-w - 5, 4), self._headers[i])
            painter.drawText(QPointF(8, 4), f"{self._values[i] * 100:.0f}")
            painter.restore()

    def __orientationLines(self, painter: QPainter, outer_ellipse: QPainterPath) -> List[QPainterPath]:
        """
        Helferlinien für die Fortschritte, da diese mit pointAtPercent bewegt werden
        :param painter:
        :param outer_ellipse:
        :return:
        """
        l: List[QPainterPath] = []
        for i, header in enumerate(self._headers):
            line: QPainterPath = QPainterPath(outer_ellipse.boundingRect().center())
            line.lineTo(outer_ellipse.pointAtPercent(i / (len(self._headers) ) ))
            painter.drawPath(line)
            l.append(line)
        return l

    # noinspection PyMethodMayBeStatic
    def __validate_headers(self, headers: List[str]) -> None:
        """
        Validierung der Header
        :param headers:
        :return:
        """
        if not all(isinstance(header, str) for header in headers):
            raise TypeError("Alle Typen der Werte müssen ein float sein")

        if not all(len(header) > 1 for header in headers):
            raise ValueError("Ein Header muss mindestens zwei Charaktere enthalten.")

        if not headers or len(headers) < 4:
            raise ValueError("Es müssen mindestens 4 Header gesetzt werden!")

    def __validate_headers_values(self, headers: List[str], values: List[float]):
        """
        Validiert Header und Values
        :param headers:
        :param values:
        :return:
        """
        self.__validate_headers(headers)
        self.__validate_values(values)
        if len(headers) != len(values):
            raise ValueError(f"Die Länge der Einträge der Header und der Werte stimmt nicht überein."
                             f"\nHeaders: '{len(headers)}'"
                             f"\nWerte: '{len(values)}'")

    # noinspection PyMethodMayBeStatic
    def __validate_values(self, values: List[float]) -> None:
        """
        Validierung der Values
        :param values:
        :return:
        """
        if not all(isinstance(value, (int, float)) for value in values):
            raise TypeError("Alle Typen der Werte müssen ein float sein")

        if not values or len(values) < 4:
            raise ValueError("Es müssen mindestens 4 Werte gesetzt werden!")
