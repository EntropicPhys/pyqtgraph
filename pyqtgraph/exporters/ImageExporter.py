from .Exporter import Exporter
from ..parametertree import Parameter
from ..Qt import QtGui, QtCore, QtSvg, QT_LIB
from .. import functions as fn
import numpy as np

translate = QtCore.QCoreApplication.translate
__all__ = ['ImageExporter']

class ImageExporter(Exporter):
    Name = f"{translate('Exporter', 'Image File')} (PNG, TIF, JPG, ...)"
    allowCopy = True
    
    def __init__(self, item):
        Exporter.__init__(self, item)
        tr = self.getTargetRect()
        if isinstance(item, QtGui.QGraphicsItem):
            scene = item.scene()
        else:
            scene = item
        bgbrush = scene.views()[0].backgroundBrush()
        bg = bgbrush.color()
        if bgbrush.style() == QtCore.Qt.NoBrush:
            bg.setAlpha(0)
            
        self.params = Parameter(name='params', type='group', children=[
            {'name': translate("Exporter", 'width'), 'type': 'int', 'value': int(tr.width()), 'limits': (0, None)},
            {'name': translate("Exporter", 'height'), 'type': 'int', 'value': int(tr.height()), 'limits': (0, None)},
            {'name': translate("Exporter", 'antialias'), 'type': 'bool', 'value': True},
            {'name': translate("Exporter", 'background'), 'type': 'color', 'value': bg},
            {'name': translate("Exporter", 'invertValue'), 'type': 'bool', 'value': False}
        ])
        self.params.param(translate("Exporter", 'width')).sigValueChanged.connect(self.widthChanged)
        self.params.param(translate("Exporter", 'height')).sigValueChanged.connect(self.heightChanged)
        
    def widthChanged(self):
        sr = self.getSourceRect()
        ar = float(sr.height()) / sr.width()
        self.params.param(translate("Exporter", 'height')).setValue(int(self.params[translate("Exporter", 'width')] * ar), blockSignal=self.heightChanged)
        
    def heightChanged(self):
        sr = self.getSourceRect()
        ar = float(sr.width()) / sr.height()
        self.params.param(translate("Exporter", 'width')).setValue(int(self.params[translate("Exporter", 'height')] * ar), blockSignal=self.widthChanged)
        
    def parameters(self):
        return self.params

    @staticmethod
    def getSupportedImageFormats():
        filter    = ["*."+f.data().decode('utf-8') for f in QtGui.QImageWriter.supportedImageFormats()]
        preferred = ['*.png', '*.tif', '*.jpg']
        for p in preferred[::-1]:
            if p in filter:
                filter.remove(p)
                filter.insert(0, p)
        return filter  

    def export(self, fileName=None, toBytes=False, copy=False):
        if fileName is None and not toBytes and not copy:
            filter = self.getSupportedImageFormats()
            self.fileSaveDialog(filter=filter)
            return

        w = int(self.params[translate("Exporter", 'width')])
        h = int(self.params[translate("Exporter", 'height')])
        if w == 0 or h == 0:
            raise Exception("Cannot export image with size=0 (requested "
                            "export size is %dx%d)" % (w, h))

        targetRect = QtCore.QRect(0, 0, w, h)
        sourceRect = self.getSourceRect()

        bg = np.empty((h, w, 4), dtype=np.ubyte)
        color = self.params[translate("Exporter", 'background')]
        bg[:,:,0] = color.blue()
        bg[:,:,1] = color.green()
        bg[:,:,2] = color.red()
        bg[:,:,3] = color.alpha()

        self.png = fn.makeQImage(bg, alpha=True, copy=False, transpose=False)
        self.bg = bg
        
        ## set resolution of image:
        origTargetRect = self.getTargetRect()
        resolutionScale = targetRect.width() / origTargetRect.width()
        #self.png.setDotsPerMeterX(self.png.dotsPerMeterX() * resolutionScale)
        #self.png.setDotsPerMeterY(self.png.dotsPerMeterY() * resolutionScale)
        
        painter = QtGui.QPainter(self.png)
        #dtr = painter.deviceTransform()
        try:
            self.setExportMode(True, {
                'antialias': self.params[translate("Exporter", 'antialias')],
                'background': self.params[translate("Exporter", 'background')],
                'painter': painter,
                'resolutionScale': resolutionScale})
            painter.setRenderHint(QtGui.QPainter.Antialiasing, self.params[translate("Exporter", 'antialias')])
            self.getScene().render(painter, QtCore.QRectF(targetRect), QtCore.QRectF(sourceRect))
        finally:
            self.setExportMode(False)
        painter.end()
        
        if self.params['invertValue']:
            mn = bg[...,:3].min(axis=2)
            mx = bg[...,:3].max(axis=2)
            d = (255 - mx) - mn
            bg[...,:3] += d[...,np.newaxis]
        
        if copy:
            QtGui.QApplication.clipboard().setImage(self.png)
        elif toBytes:
            return self.png
        else:
            return self.png.save(fileName)
        
ImageExporter.register()        
        
