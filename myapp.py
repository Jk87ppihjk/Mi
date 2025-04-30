# Salve este arquivo como "app.py" ou outro nome no Pydroid3
# Rode normalmente no Kivy Launcher ou pelo Pydroid3

from kivy.core.window import Window
from kivy.lang import Builder
from kivy.utils import get_color_from_hex
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.properties import NumericProperty
import os
import json

Window.clearcolor = get_color_from_hex("#121212")
NOTES_FILE = "minhas_notas.json"

class NoteScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.notes_data = self.load_notes()

        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        layout.add_widget(Label(text="Minhas Notas", font_size=28, color=[1, 1, 1, 1], size_hint_y=0.1))

        self.note_input = TextInput(hint_text="Digite sua nota aqui...",
                                    background_color=get_color_from_hex("#1E1E1E"),
                                    foreground_color=[1, 1, 1, 1],
                                    cursor_color=[1, 1, 1, 1],
                                    size_hint_y=0.3)
        layout.add_widget(self.note_input)

        add_btn = Button(text="Nova Nota", background_color=get_color_from_hex("#03DAC6"), size_hint_y=0.1)
        add_btn.bind(on_press=self.add_note)
        layout.add_widget(add_btn)

        self.notes_container = GridLayout(cols=1, spacing=10, size_hint_y=None)
        self.notes_container.bind(minimum_height=self.notes_container.setter('height'))
        scroll = ScrollView(size_hint_y=0.4)
        scroll.add_widget(self.notes_container)
        layout.add_widget(scroll)

        comp_btn = Button(text="Modo Compositor", background_color=get_color_from_hex("#BB86FC"), size_hint_y=0.1)
        comp_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'compositor'))
        layout.add_widget(comp_btn)

        self.refresh_notes()
        self.add_widget(layout)

    def load_notes(self):
        try:
            with open(NOTES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return []
        except json.JSONDecodeError:
            return []

    def save_notes(self):
        try:
            with open(NOTES_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.notes_data, f)
        except Exception as e:
            print(f"Erro ao salvar notas: {e}")

    def add_note(self, _):
        text = self.note_input.text.strip()
        if text:
            self.notes_data.append(text)
            self.note_input.text = ""
            self.refresh_notes()
            self.save_notes()

    def refresh_notes(self):
        self.notes_container.clear_widgets()
        for i, note in enumerate(self.notes_data):
            btn = Button(text=note.split("\n")[0][:50], size_hint_y=None, height=60,
                         background_color=get_color_from_hex("#272727"),
                         color=[1, 1, 1, 1])
            btn.bind(on_release=lambda _, idx=i: self.edit_note(idx))
            self.notes_container.add_widget(btn)

    def edit_note(self, index):
        def salvar(_):
            self.notes_data[index] = edit_input.text
            popup.dismiss()
            self.refresh_notes()
            self.save_notes()

        edit_input = TextInput(text=self.notes_data[index],
                               background_color=get_color_from_hex("#1E1E1E"),
                               foreground_color=[1, 1, 1, 1])
        salvar_btn = Button(text="Salvar", background_color=get_color_from_hex("#03DAC6"), size_hint_y=0.2)
        salvar_btn.bind(on_release=salvar)

        box = BoxLayout(orientation='vertical')
        box.add_widget(edit_input)
        box.add_widget(salvar_btn)

        popup = Popup(title="Editar Nota", content=box, size_hint=(0.9, 0.9))
        popup.open()

class CompositorScreen(Screen):
    num_letras_rima = NumericProperty(3)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rimas = []
        self.rima_index = 0
        self.ultima_palavra = ""
        self.banco_path = ""
        self.load_banco() # Carrega o banco de palavras ao iniciar

        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        config_layout = BoxLayout(orientation='horizontal', size_hint_y=0.1, spacing=5)
        label_config = Label(text="Analisar últimas:", color=[1, 1, 1, 1])
        self.input_num_letras = TextInput(text=str(self.num_letras_rima), input_type='number', input_filter='int',
                                          size_hint_x=0.3, background_color=get_color_from_hex("#1E1E1E"),
                                          foreground_color=[1, 1, 1, 1], cursor_color=[1, 1, 1, 1])
        self.input_num_letras.bind(text=self.on_num_letras_change)
        config_layout.add_widget(label_config)
        config_layout.add_widget(self.input_num_letras)
        layout.add_widget(config_layout)

        self.input_palavra = TextInput(hint_text="Digite uma palavra", size_hint_y=0.1,
                                       background_color=get_color_from_hex("#1E1E1E"),
                                       foreground_color=[1, 1, 1, 1],
                                       cursor_color=[1, 1, 1, 1])
        layout.add_widget(self.input_palavra)

        self.resultado_label = Label(text="", halign='center', valign='middle', size_hint_y=0.4,
                                     text_size=(Window.width - 20, None), color=[1, 1, 1, 1])
        scroll = ScrollView()
        scroll.add_widget(self.resultado_label)
        layout.add_widget(scroll)

        btn_rimar = Button(text="Procurar Rima", size_hint_y=0.1, background_color=get_color_from_hex("#03DAC6"))
        btn_rimar.bind(on_press=self.encontrar_rimas)
        layout.add_widget(btn_rimar)

        btn_importar = Button(text="Importar Banco", size_hint_y=0.1, background_color=get_color_from_hex("#4CAF50"))
        btn_importar.bind(on_press=self.importar_banco_popup) # Renomeado para clareza
        layout.add_widget(btn_importar)

        btn_voltar = Button(text="Voltar", size_hint_y=0.1, background_color=get_color_from_hex("#BB86FC"))
        btn_voltar.bind(on_press=lambda _: setattr(self.manager, 'current', 'notas'))
        layout.add_widget(btn_voltar)

        self.add_widget(layout)

    def load_banco(self):
        # Tenta carregar o banco de palavras salvo, se existir
        try:
            with open("banco_palavras.txt", 'r', encoding='utf-8') as f:
                self.banco_path = "banco_palavras.txt"
        except FileNotFoundError:
            self.banco_path = "" # Banco ainda não foi importado

    def on_num_letras_change(self, instance, value):
        try:
            self.num_letras_rima = int(value)
        except ValueError:
            self.num_letras_rima = 1 # Garante um valor padrão caso a entrada seja inválida

    def importar_banco_popup(self, _):
        content = BoxLayout(orientation='vertical')
        filechooser = FileChooserListView(filters=["*.txt"], path='.')
        btn = Button(text="Selecionar", size_hint_y=0.2)

        def escolher(instance):
            if filechooser.selection:
                self.banco_path = filechooser.selection[0]
                # Copia o arquivo selecionado para o nome padrão "banco_palavras.txt"
                try:
                    with open(self.banco_path, 'r', encoding='utf-8') as src, \
                         open("banco_palavras.txt", 'w', encoding='utf-8') as dest:
                        dest.write(src.read())
                    self.banco_path = "banco_palavras.txt" # Atualiza para o novo caminho
                    popup.dismiss()
                    self.resultado_label.text = f"Banco carregado e salvo:\n{os.path.basename(self.banco_path)}"
                except Exception as e:
                    self.resultado_label.text = f"Erro ao importar/salvar banco: {str(e)}"

        btn.bind(on_press=escolher)
        content.add_widget(filechooser)
        content.add_widget(btn)

        popup = Popup(title="Importar banco de palavras", content=content, size_hint=(0.9, 0.9))
        popup.open()

    def encontrar_rimas(self, _):
        if not self.banco_path:
            self.resultado_label.text = "Importe um banco de palavras primeiro."
            return

        palavra = self.input_palavra.text.strip().lower()
        if not palavra:
            self.resultado_label.text = "Digite uma palavra!"
            return

        num_letras = max(1, self.num_letras_rima) # Garante que pelo menos 1 letra seja comparada
        if len(palavra) < num_letras:
            self.resultado_label.text = f"A palavra precisa ter pelo menos {num_letras} letras."
            return
        terminacao = palavra[-num_letras:]

        try:
            with open(self.banco_path, 'a+', encoding='utf-8') as f:
                f.seek(0)
                palavras = set(l.strip().lower() for l in f if l.strip()) # Usar set para evitar duplicatas
                if palavra not in palavras:
                    f.write(palavra + "\n")
                    palavras.add(palavra)
                palavras_lista = sorted(list(palavras)) # Converter de volta para lista ordenada

            if palavra != self.ultima_palavra or self.num_letras_rima != getattr(self, 'anterior_num_letras_rima', None):
                self.rimas = [p for p in palavras_lista if p != palavra and len(p) >= num_letras and p[-num_letras:] == terminacao]
                self.rimas.sort()
                self.rima_index = 0
                self.ultima_palavra = palavra
                self.anterior_num_letras_rima = self.num_letras_rima

            if self.rima_index < len(self.rimas):
                fim = self.rima_index + 10 # Aumentei para mostrar mais rimas por vez
                mostrar = "\n".join(self.rimas[self.rima_index:fim])
                self.rima_index = fim
                self.resultado_label.text = f"Rimas ({num_letras} letras finais):\n{mostrar}"
            else:
                self.resultado_label.text = "Fim das rimas.\nContinue me usando\npara me deixar\nmais inteligente!"
        except Exception as e:
            self.resultado_label.text = f"Erro: {str(e)}"

class BlocoApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(NoteScreen(name="notas"))
        sm.add_widget(CompositorScreen(name="compositor"))
        return sm

if __name__ == '__main__':
    BlocoApp().run()
