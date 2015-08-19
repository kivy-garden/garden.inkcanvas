'''
StrokeCanvas Demonstration
=======================================

This demonstrates the use of a StrokeCanvas, properties and behavior that can
be changed. It binds as well events produced for the StrokeCanvas.
Additionally, it shows the bounding box of a stroke with a fade rectangle.

'''

from kivy.app import App
from kivy.uix.inkcanvas import StrokeCanvasBehavior, Stroke, StrokeRect,\
        StrokePoint, Sample, NDolarRecognizer
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.graphics import Color, Rectangle
from kivy.uix.textinput import TextInput
from functools import partial
import os
import six


class StrokeCanvasFloat(StrokeCanvasBehavior, FloatLayout):
    pass


class StrokeCanvasTest(App):
    title = 'InkCanvas'
    strokes_collected = []
    drawn = False
    sample = {}
    samples = []
    fig, ax = None, None

    def callback(self, button, result, *args):
        if self.inkc.mode == 'draw':
            self.inkc.mode = 'erase'
            button.text = 'Erase Mode'
        elif self.inkc.mode == 'erase':
            self.inkc.mode = 'draw'
            button.text = 'Draw Mode'

    def stroke_collected(self, layout, stroke):
        self.strokes_collected.append(stroke)

    def stroke_removed(self, layout, strk):
        pass

    def mode_changed(self, instance, value):
        pass

    def build(self):
        self.layout = FloatLayout()
        self.inkc = inkc = StrokeCanvasFloat(size_hint=(1, .90))
        inkc.stroke_color = 'darkblue'
        inkc.stroke_width = 2.0
        inkc.stroke_visibility = True
        inkc.stroke_opacity = 0.8
        inkc.bind(size=self._update_rect, pos=self._update_rect)
        inkc.bind(on_stroke_added=self.stroke_collected)
        inkc.bind(on_stroke_removed=self.stroke_removed)
        inkc.bind(mode=self.mode_changed)
        btn_mode = Button(text='Draw Mode', size_hint=(1, .10),
                     pos_hint={'top': 1.0})
        btn_mode.bind(on_press=partial(self.callback, btn_mode))
        boxlayout = BoxLayout(orientation="horizontal", size_hint=(1, .10),
                            pos_hint={'bottom': 1.0})
        textinput = TextInput(text="")
        btn_train = Button(text='Train')
        btn_train.bind(on_press=partial(self.train_btn, textinput))
        btn_load = Button(text='Load')
        btn_load.bind(on_press=self.load_btn)
        btn_recognize = Button(text='Recognize')
        btn_recognize.bind(on_press=partial(self.recognize_btn, textinput))
        btn_clear = Button(text='Clear')
        btn_clear.bind(on_press=self.clear_btn)
        boxlayout.add_widget(textinput)
        boxlayout.add_widget(btn_train)
        boxlayout.add_widget(btn_load)
        boxlayout.add_widget(btn_recognize)
        boxlayout.add_widget(btn_clear)
        with inkc.canvas.before:
            Color(1.0, 1.0, 1.0, 1.0)
            self.rect = Rectangle(size=inkc.size, pos=inkc.pos)
        self.layout.add_widget(inkc)
        self.layout.add_widget(btn_mode)
        self.layout.add_widget(boxlayout)
        return self.layout

    def clear_btn(self, result, *args):
        self.inkc.canvas.clear()
        self.inkc.strokes = []
        self.strokes_collected = []

    def load_btn(self, result, *args):
        self.samples = []
        path = os.path.join(os.getcwd(), "samples")
        if os.path.exists(path):
            for root, dirs, files in os.walk(path):
                for dir in dirs:
                    list_samples = []
                    samples_dir = os.path.join(path, dir)
                    for root2, dirs2, files2 in os.walk(samples_dir):
                        for name in files2:
                            strk_list = self.inkc.load(
                                            os.path.join(samples_dir, name))
                            list_samples.append(strk_list)
                    smpl = Sample(dir, list_samples)
                    self.samples.append(smpl)

    def train_btn(self, textinput, result, *args):
        path = os.path.join(os.getcwd(), "samples")
        if not os.path.exists(path):
            os.makedirs(path)

        if textinput.text not in self.sample.keys():
            path_train = os.path.join(path, textinput.text)
            if not os.path.exists(path_train):
                os.makedirs(path_train)
        if six.PY2:
            num_files = len(os.walk(path_train).next()[2])
        elif six.PY3:
            num_files = len(os.walk(path_train).__next__()[2])
        file_name = textinput.text + "{}".format(num_files)
        self.inkc.save(file_name, os.path.join(path_train, file_name))
        self.inkc.canvas.clear()
        self.inkc.strokes = []
        self.strokes_collected = []

    def recognize_btn(self, textinput, result, *args):
        if len(self.samples) == 0:
            self.load_btn(result)
        recognizer = NDolarRecognizer()
        sel = recognizer.combine_strokes(self.strokes_collected)
        sel.filtering()
        sel.points = recognizer.resample(sel.filtered_points, 96.0)
        if len(sel.points):
            w = recognizer.indicative_angle(sel.points)
            sel.points = recognizer.rotate_by(sel.points, -w)
            sel.points = recognizer.scale_dim_to(sel.points, size=250.0, d=0.3)
            sel.points = recognizer.check_restore_orientation(sel.points, w)
            sel.points = recognizer.translate_to(sel.points, recognizer.O)
            sel.vector = recognizer.calc_start_unit_vector(sel.points,
                                                           recognizer.I)
            outcome = recognizer.recognize(sel, sel.vector,
                                    len(self.strokes_collected), self.samples)
            if outcome[1] > 0.7:
                textinput.text = "{}".format(outcome[2])
                print ("There is " + "{:.2f}".format(outcome[1] * 100) +
                       " probability is " + "{}".format(outcome[2]))
            else:
                textinput.text = "nan"
                print ("Score too low not recognized")
        else:
            print ("Not enough information")

    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size

    def on_pause(self):
        return True

if __name__ == '__main__':
    StrokeCanvasTest().run()

