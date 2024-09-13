import requests,os, spacy ,psycopg2 ,random
from concurrent.futures import ThreadPoolExecutor
from PIL import Image
from io import BytesIO
from dotenv import load_dotenv
from openai import OpenAI
from moviepy.editor import AudioFileClip, ImageClip, TextClip, CompositeVideoClip, VideoFileClip,concatenate_videoclips
from transformers import BlipProcessor, BlipForConditionalGeneration
from moviepy.video.fx.all import resize , fadein, fadeout
from moviepy.config import change_settings
from AgentFunctions import *














class Scene:

    def __init__(self,scene_type:str,scene_data:dict,uuid:str,output_dir:str,frame_rate:int,scene_chunk_len:int):
        self.scene_data = scene_data
        self.scene_chunk_len = scene_chunk_len
        self.scene_type = scene_type
        self.output_dir = output_dir
        self.fps = frame_rate
        self.uuid = uuid
        self.gpt_model = os.getenv('MODEL_NAME')
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.videos = []
        self.init_scene()

    # --------------------------------------Creating Scene-------------------------------------
    def init_scene(self):
        if self.scene_type == "intro":
            self.create_intro_scene()
        elif self.scene_type == "outro":
            return 
        else:    
            self.create_scene()
    
    def create_intro_scene(self):
        save_dir = os.path.join(self.output_dir, f'{self.uuid}/save/intro/')
        os.makedirs(save_dir, exist_ok=True)

        intro = VideoFileClip('assets/marea_intro.mov')
        video = CompositeVideoClip([intro])
        
        output_video_path = os.path.join(save_dir, 'intro1.mp4')
        video.write_videofile(output_video_path,fps=self.fps,preset='ultrafast',logger=None,threads=4)
        self.videos.append(output_video_path)
        # --------------------------------------welcome-------------------------------------
        intro = VideoFileClip('assets/into2.mp4')
        video = CompositeVideoClip([intro])
        
        output_video_path = os.path.join(save_dir, 'intro2.mp4')
        video.write_videofile(output_video_path,fps=self.fps,preset='ultrafast',logger=None,threads=4)
        self.videos.append(output_video_path)

    def create_scene(self):
        first_section = True
        
        if 'images' not in self.scene_data:
            print(f"No images found for scene: {self.scene_data}")
            return
        
        for image_info in self.scene_data['images'][:self.scene_chunk_len]:
            image,details,script = image_info['image'], image_info['details'] , image_info['script']
        
            print(image, "->", details,"script->", script)
            self.create_video_from_script(script,image,first_section)
            first_section = False

    def create_video_from_script(self, script: str, image: str,isFirst:bool = False):
        template = []
        image_dir = os.path.join(self.output_dir, f'{self.uuid}/{image}')
        save_dir = os.path.join(self.output_dir, f'{self.uuid}/save/{self.scene_type}/')
        temp_audio_path = os.path.join(save_dir, f"temp_audio_{image.replace('.jpg', '')}.wav")
        os.makedirs(save_dir, exist_ok=True)

        # Generate audio from the script
        audio_buffer = self.ttsApi(script)
        with open(temp_audio_path, "wb") as f:
            f.write(audio_buffer.read())

        audio_clip = AudioFileClip(temp_audio_path)
        
        if isFirst:
            template_func = random.choice([self.template1, self.template2])
            template = template_func(script, image_dir, audio_clip.duration)
        else:
            template_func = random.choice([self.template3, self.template4])
            template = template_func(script, image_dir, audio_clip.duration)
        
        
        video = CompositeVideoClip(template).set_audio(audio_clip)
        output_video_path = f'{save_dir}/{image.replace(".jpg", "")}.mp4'
        video.write_videofile(output_video_path,fps=self.fps,preset='ultrafast',logger=None)
        self.videos.append(output_video_path)

        if temp_audio_path and os.path.exists(temp_audio_path):
            os.remove(temp_audio_path)
    
    
    # ------------------------------------Templates Functions-----------------------------------

    def template1(self,script:str,image_dir:str,duration:float)->list:
        title = self.scene_type.capitalize() + " Details"
        subtitle = self.scene_data['dataBaseData']
        subtitle =self.gpt_call(self.get_prompt_db(subtitle))

        # subtitle = "• MLSPropertyType: residential lease \n\n• MLSListingAddress: 14063 Wool Park Title"
        print('gpt->',subtitle,'Title->',title)
     
        image_bg = ImageClip(image_dir).set_duration(duration)
        image_bg_layer1 = ImageClip('assets/template1/template1_bg.png').set_duration(duration).resize(newsize=image_bg.size)
        
        title = TextClip(title, fontsize=90, font='Arial-Bold', color='white')
        title = self.fx_slide_in_from_left(title, animation_duration=0.9,total_duration=duration, final_x=image_bg.w*0.04, y_pos=image_bg.h*0.16)   

        text = TextClip(subtitle, fontsize=40,align='west',font='Arial-Light', color='white')
        text = self.fx_slide_in_from_left(text, animation_duration=0.9,total_duration=duration, final_x=image_bg.w*0.05, y_pos=image_bg.h*0.3)   

        title_bg = ImageClip('assets/template1/bar_bg.png').set_duration(duration).resize(newsize=(image_bg.w*0.7, image_bg.h*0.4))
        title_bg = self.fx_slide_in_from_left(title_bg, animation_duration=0.9,total_duration=duration, final_x=0, y_pos=image_bg.h*0.1)
        
        image_bg = self.fx_zoom_rand(image_bg, duration)
        image_blur = ImageClip('assets/bottom_blur.png').set_duration(duration)
        subtitle_clip = self.create_subtitle_clips(script, (image_bg.w, image_bg.h), duration,align='left')

        return [image_bg, image_blur,image_bg_layer1,title_bg,title,text] + subtitle_clip

    def template2(self,script:str,image_dir:str,duration:float)->list:
        title = self.scene_type.capitalize() + " Details"
        subtitle = self.scene_data['dataBaseData']
        subtitle =self.gpt_call(self.get_prompt_db(subtitle,3))

        # subtitle = "• MLSPropertyType: residential lease \n\n• MLSListingAddress: 14063 Wool Park Title\n\n• MLSListingAddress: 14063 Wool Park Title"
        subtitle = "    "+subtitle.replace(':',':\n  ').replace("\n\n", "\n\n  ", 1)
        print('gpt->',subtitle,'Title->',title)   
     
        image_bg = ImageClip(image_dir).set_duration(duration)
        slide_left = VideoFileClip('assets/template2/template2_anim.gif',has_mask=True).set_duration(duration).resize(newsize=image_bg.size).set_opacity(0.65)

        title = TextClip(title, fontsize=85, font='Arial-Bold', color='white')
        title = self.fx_slide_in_from_right(title, animation_duration=0.9,total_duration=duration, final_x=image_bg.w*0.56, y_pos=image_bg.h*0.77,start_x=image_bg.w*1.5)   

        text = TextClip(subtitle, fontsize=45,align='west',font='Arial-Light', color='white')
        text = self.fx_slide_in_from_right(text, animation_duration=0.9,total_duration=duration, final_x=image_bg.w*0.6, y_pos=image_bg.h*0.3,start_x=image_bg.w*1.5)   

        image_bg = self.fx_zoom_rand(image_bg, duration)
        subtitle_clip = self.create_subtitle_clips(script, (image_bg.w, image_bg.h), duration,align='right')

        return [image_bg,slide_left,title,text] + subtitle_clip       

    def template3(self,script:str,image_dir:str,duration:float)->list:
        title = self.scene_type.capitalize() + " Details"
        subtitle = self.scene_data['dataBaseData']
        subtitle =self.gpt_call(self.get_prompt_db(subtitle))

        # subtitle = "• MLSPropertyType: residential lease \n\n• MLSListingAddress: 14063 Wool Park Title"
        print('gpt->',subtitle,'Title->',title)
     
        image_bg = ImageClip(image_dir).set_duration(duration)

        title = TextClip(title, fontsize=90, font='Arial-Bold', color='white')
        title = self.fx_slide_in_from_right(title, animation_duration=0.9,total_duration=duration, final_x=image_bg.w*0.45, y_pos=image_bg.h*0.16,start_x=image_bg.w*1.5)   

        text = TextClip(subtitle, fontsize=40,align='west',font='Arial-Light', color='white')
        text = self.fx_slide_in_from_right(text, animation_duration=0.9,total_duration=duration, final_x=image_bg.w*0.45, y_pos=image_bg.h*0.3,start_x=image_bg.w*1.5)   

        title_bg = ImageClip('assets/template1/bar_bg.png').set_duration(duration).resize(newsize=(image_bg.w*0.7, image_bg.h*0.4))
        title_bg = self.fx_slide_in_from_right(title_bg, animation_duration=0.9,total_duration=duration, final_x=image_bg.w*0.4, y_pos=image_bg.h*0.11,start_x=image_bg.w*1.5)


        image_blur = ImageClip('assets/bottom_blur.png').set_duration(duration).resize(newsize=image_bg.size)
        image_bg = self.fx_zoom_rand(image_bg, duration)
        subtitle_clip = self.create_subtitle_clips(script, (image_bg.w, image_bg.h), duration,align='center')

        return [image_bg, image_blur,title_bg,title,text] + subtitle_clip   

    def template4(self,script:str,image_dir:str,duration:float)->list:
        
        image_bg = ImageClip(image_dir).set_duration(duration)
        image_bg = self.fx_zoom_rand(image_bg, duration)
        image_blur = ImageClip('assets/bottom_blur.png').set_duration(duration).resize(newsize=image_bg.size)
        subtitle_clip = self.create_subtitle_clips(script, (image_bg.w, image_bg.h), duration,align='center')
        
        return [image_bg,image_blur] + subtitle_clip


    #  ------------------------------------Text Caption Functions-----------------------------------
    def split_script_into_lines(self,script, words_per_line=5)->list:
        script_words = script.split()
        script_lines = [' '.join(script_words[i:i + words_per_line]) for i in range(0, len(script_words), words_per_line)]
        return script_lines

    def create_subtitle_clips(self, script: str, size: tuple, duration: float,align:str = 'center', fontsize:int = 26):
        w, h = size  # Unpack width and height from the size tuple

        if align == 'right':
            x_pos = h *0.29
        elif align == 'left':
            x_pos = -h *0.33
        else:
            x_pos = 0

        script_lines = self.split_script_into_lines(script, words_per_line=8)
        num_lines = len(script_lines)
        duration_per_line = duration / num_lines
        
        subtitle_clips = []
        
        for i, line in enumerate(script_lines):
            subtitle = TextClip(line, fontsize=fontsize, font='Arial-Bold', size=(w,h), color='white', method='caption')
            subtitle = subtitle.set_duration(duration_per_line).set_position((x_pos, h*0.46)).set_start(i * duration_per_line)
            subtitle_clips.append(subtitle)
        
        return subtitle_clips


    # ------------------------------------FX Functions-----------------------------------
    def fx_slide_in_from_left(self, elem, animation_duration: float, total_duration: float, final_x: float, y_pos='center',start_x:float = None) -> ImageClip:
        if start_x is None:
            start_x = -elem.w
        return elem.set_duration(total_duration) \
            .set_position(lambda t: (start_x + (final_x - start_x) * (t / animation_duration) if t <= animation_duration else final_x, y_pos))

    def fx_slide_in_from_right(self, elem, animation_duration: float, total_duration: float, final_x: float, y_pos='center',start_x:float = None) -> ImageClip:
        if start_x is None:
            start_x = elem.w  
        return elem.set_duration(total_duration) \
            .set_position(lambda t: (start_x + (final_x - start_x) * (t / animation_duration) if t <= animation_duration else final_x, y_pos))

    def fx_zoom_rand(self, elem: ImageClip, duration: float) -> ImageClip:
        if random.choice([True,False]):
            elem = self.fx_zoomin_center(elem, duration,zoom=random.uniform(0.2, 0.8))
        else:
            elem = self.fx_zoomin_topleft(elem, duration,zoom=random.uniform(0.2, 0.8))
        return elem

    def fx_zoomin_center(self, elem: ImageClip, duration: float, zoom: float = 0.25) -> ImageClip:
        def zoom_effect(t):
            scale = 1 + zoom * (t / duration)
            return scale
        return elem.fx(resize, zoom_effect).set_position('center')
    
    def fx_zoomin_topleft(self,elem: ImageClip, duration: float,zoom:float = 0.25)->ImageClip:
        return elem.fx(resize, lambda t: 1 + zoom * t / duration)

    def fx_fadein(self, elem: ImageClip, duration: float) -> ImageClip:
        return elem.fx(fadein, duration)

    def fx_fadeout(self, elem: ImageClip, duration: float) -> ImageClip:
        return elem.fx(fadeout, duration)


    # ------------------------------------Gpt Script Functions-----------------------------------
    def ttsApi(self,text,agentName="marea"):
        buffer = None
        if agentName == "marea":
            agentName = "shimmer"
        else:
            agentName = "onyx"
        try:
            spoken_response = self.client.audio.speech.create(
                model="tts-1",
                voice=agentName,
                response_format="wav",
                input=text
            )

            buffer = BytesIO()
            for chunk in spoken_response.iter_bytes(chunk_size=4096):
                buffer.write(chunk)
            buffer.seek(0)
        except Exception as e:
            print(f"An error occurred in TTS: {e}")
        finally:
            return buffer
  
    def get_prompt_db(self,db:str,len:int=2)->str:
        return f'''I am going to provide you with a dicitonary your job is to provide {len} most imporant key value pairs.
            The Scene you are currenlty working on is: {self.scene_type}
            Always give me the key value pairs.
            only give these {len} in response to the user.
            Always keep response short.
            Try not to use null or empery values. Try to select the key that have value. 
            As these vatues are directly from database so do not mention keword of database etc in your response this responce is for a non tech person.
            The key value pairs are:
            {db}
            Give output in this exact format for example:
            • key name: Value of the key \n
            • key name: Value of the key
            '''

    def gpt_call(self, input: str) -> str:
        try:
            messages = [{"role": "user", "content": input}]              
            result = self.client.chat.completions.create(model=self.gpt_model, messages=messages)
            script = result.choices[0].message.content

        except Exception as e:
            print(f"An error occurred in gpt_call: {e}")
        
        return script  
