import customtkinter as ctk
from customtkinter import filedialog
import tkinter as tk
from PIL import Image, ImageTk, ImageDraw, ImageFont, ImageColor
import platform

FONT_MAP = {
    "Arial": {
        "Windows": "C:/Windows/Fonts/arial.ttf",
        "Darwin": "/System/Library/Fonts/Supplemental/Arial.ttf",
        "Linux": "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    },
    "Times New Roman": {
        "Windows": "C:/Windows/Fonts/times.ttf",
        "Darwin": "/System/Library/Fonts/Supplemental/Times New Roman.ttf",
        "Linux": "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"
    }
}

def apply_text_with_opacity(image, text, font_name, font_size, position, color, opacity):
    """Apply semi-transparent text to a PIL image and return the composited result."""
    if not text:
        return image

    txt_layer = Image.new("RGBA", image.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(txt_layer)

    sys_platform = platform.system()
    font_path = FONT_MAP.get(font_name, {}).get(sys_platform)

    try:
        font = ImageFont.truetype(font_path, font_size) if font_path else ImageFont.load_default()
    except:
        font = ImageFont.load_default()

    alpha = max(0, min(255, int(opacity * 2.55)))

    try:
        rgb = ImageColor.getrgb(color)
    except:
        rgb = (255, 255, 255)

    rgba_color = rgb + (alpha,)

    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x, y = position
    x -= text_width // 2
    y -= text_height // 2

    draw.text((x, y), text, font=font, fill=rgba_color)
    return Image.alpha_composite(image, txt_layer)


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        # Main Setup
        self.title('Watermark Generator')
        self.geometry("600x500")
        self.resizable(False, False)

        self.img_label = None
        self.image_id = None
        self.text_id = None
        self.tk_img = None
        self.base_img = None
        self.last_rendered_img = None
        self.current_opacity = 100

        self.top_container = ctk.CTkFrame(self)
        self.top_container.pack(side="top", fill="both", expand=True, padx=20, pady=10)

        # Frame 1 Setup (Image editing)
        self.frame1 = ctk.CTkFrame(self.top_container)
        self.frame1.pack(side='left', pady=10, padx=10, fill="y", expand=False)

        self.btn_upload = ctk.CTkButton(self.frame1, text='Select Image', command=self.get_image)
        self.btn_upload.grid(row=1, column=1,  padx=10, pady=(60,0))

        self.btn_save_as = ctk.CTkButton(self.frame1, text='Save As', command=self.save_image)
        self.btn_save_as.grid(row=2, column=1, padx=10, pady=(60,0))
        
        # Frame 2 Setup (Image Showcase)
        self.frame2 = ctk.CTkFrame(self.top_container)
        self.frame2.pack(side='left', pady=10, padx=10, fill="both", expand=True)

        self.canvas = ctk.CTkCanvas(self.frame2, width=600, height=400, bg='black', highlightthickness=0)

        # Frame 3 Setup (Text Editing)
        self.frame3 = ctk.CTkFrame(self)
        self.frame3.pack(side='top', pady=20, padx=20, fill="both", expand=True)

        # Left Side
        self.lbl_text = ctk.CTkLabel(self.frame3, text='Enter Your Text Below:')
        self.lbl_text.grid(row=1, column=1, pady=0, padx=20)

        self.name_entry = ctk.CTkEntry(self.frame3, placeholder_text="Your text here")
        self.name_entry.grid(row=2, column=1, padx=20)

        self.btn_apply = ctk.CTkButton(self.frame3, text="Apply", command=self.text_entry)
        self.btn_apply.grid(row=3, column=1, padx=20)

        self.font_select = ctk.CTkComboBox(self.frame3, values=["Arial", "Times New Roman"],
                                            command=self.select_font, width=70)
        self.font_select.set("Arial")
        self.font_select.grid(row=4, column=1, padx=(0, 70))

        self.colour_select = ctk.CTkComboBox(self.frame3, values=["White", "Black"],
                                            command=self.select_colour, width=70)
        self.colour_select.set("White")
        self.colour_select.grid(row=4, column=1, padx=(70,0))

        # Middle
        self.lbl_radio = ctk.CTkLabel(self.frame3, text='Text Alignment:')
        self.lbl_radio.grid(row=1, column=2, pady=10)

        self.radio_var = tk.IntVar(value=1)
        self.radio_centre = ctk.CTkRadioButton(self.frame3, text="Centre",
                                                    command=self.radiobutton_event, variable= self.radio_var, value=1)
        self.radio_top = ctk.CTkRadioButton(self.frame3, text="Top",
                                                    command=self.radiobutton_event, variable= self.radio_var, value=2)
        self.radio_bottom = ctk.CTkRadioButton(self.frame3, text="Bottom",
                                                    command=self.radiobutton_event, variable= self.radio_var, value=3)
        
        self.radio_centre.grid(row=2, column=2, padx=20, pady=10)
        self.radio_top.grid(row=3, column=2, padx=20, pady=10)
        self.radio_bottom.grid(row=4, column=2, padx=20, pady=10)

        # Right Side 
        self.lbl_opac = ctk.CTkLabel(self.frame3, text='Opacity:')
        self.lbl_opac.grid(row=1, column=3, pady=0, padx=10)

        self.sld_opacity = ctk.CTkSlider(self.frame3, from_=0, to=100, command=self.change_opac)
        self.sld_opacity.grid(row=2, column=3, padx=20, pady=0)

        self.lbl_textsize = ctk.CTkLabel(self.frame3, text='Text Size:')
        self.lbl_textsize.grid(row=3, column=3, pady=0, padx=10)

        self.sld_textsize = ctk.CTkSlider(self.frame3, from_=0, to=100, command=self.change_textsize)
        self.sld_textsize.grid(row=4, column=3, padx=20, pady=0)

    def update_canvas_img(self):
        if not self.base_img:
            return
        
        text = self.name_entry.get()
        font_name = self.font_select.get()
        font_size = self.sld_textsize.get()
        colour = self.colour_select.get()
        opacity = self.current_opacity

        if self.radio_var.get() == 1:
            pos = (300, 200)
        elif self.radio_var.get() == 2:
            pos = (300, 40)
        else:
            pos = (300, 360)

        composited_img = apply_text_with_opacity(
            self.base_img.copy(), text, font_name, font_size, pos, colour, opacity
            )
        
        self.last_rendered_img = composited_img
        self.tk_img = ImageTk.PhotoImage(composited_img)
        self.canvas.delete("all")
        self.image_id = self.canvas.create_image(0, 0, anchor='nw', image=self.tk_img)

    def text_entry(self):
        """Change Label on img"""
        self.update_canvas_img()

    def get_image(self):
        """Get image to edit"""
        img_path = filedialog.askopenfilename(
            filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.bmp;*.gif")]
        )
        
        if img_path:
            self.display_img(img_path)
    
    def display_img(self, img_path):
        """Display image in frame once selected"""
        img = Image.open(img_path).convert('RGBA')
        img = img.resize((600,400))
        self.base_img = img

        self.canvas.pack(padx=20, pady=40)
        self.update_canvas_img()

    def save_image(self):
        """Save Updated Image"""
        if self.last_rendered_img is None:
            return

        save_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG Image", "*.png"), ("JPEG Image", "*.jpg"), ("All Files", "*.*")]
        )

        if save_path:
            self.last_rendered_img.save(save_path)

    def change_opac(self, value):
        """Change Opacity with Slider"""
        self.current_opacity = int(value)
        self.update_canvas_img()
        
    def change_textsize(self, value):
        """Change size of text"""
        self.update_canvas_img()

    def radiobutton_event(self):
        """Change position of watermark text relevant to image"""
        self.update_canvas_img()

    
    def select_font(self, font):
        """Select a font"""
        self.update_canvas_img()
    
    def select_colour(self, colour):
        """Select a font colour"""
        self.update_canvas_img()