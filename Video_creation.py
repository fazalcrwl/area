
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
from Scene import Scene
















class ConstructVideo:
    # --------------------------------------initlization-------------------------------------
    
    video=[]
    scenes = []
    uuid=''
    conn=None
    final_video_save_dir=''
    scenes_data={}
    frame_rate = 24
    threadId = ''
    
    def __init__(self, uuid: str, output_dir: str = 'tmp',scene_chunk_len:int=1):
        self.uuid = uuid
        self.output_dir = output_dir
        self.scene_chunk_len = scene_chunk_len
        self.threadId = self.create_threadId()
        self.create_db_connection()
        self.compile_video()
        self.destroy_db_connection()

    def create_db_connection(self):
        conn = psycopg2.connect(host=os.getenv('DATABASE_HOST'),database=os.getenv("DATABASE_NAME"),user=os.getenv("DATABASE_USERNAME"),
            password=os.getenv("DATABASE_PASSWORD"),port=os.getenv("DATABASE_PORT"))
        self.conn = conn

    def destroy_db_connection(self):
        self.conn.close()

    def create_threadId(self):
        thread = createThread()
        return thread.id
    
    
    # --------------------------------------Constructing Video and Senses---------------------------------------- 
    def compile_video(self):
        scenes_arr=[]
        # videoStructure = ['view','house','room','bed','bath','kitchen','patio','pool','garage','outro']
        videoStructure = ['view','house','room','bed','bath','kitchen']
        
        self.scenes_data=self.construct_senses_json()
        # self.scenes_data = {'outro': {'images': [{'image': 'photo_2.jpg', 'details': 'this is an aerial photo of a home for sale'}, {'image': 'photo_21.jpg', 'details': 'this is an aerial photo of a home for sale'}, {'image': 'photo_23.jpg', 'details': 'this is an aerial view of the home'}, {'image': 'photo_27.jpg', 'details': 'this is an aerial photo of a home for sale in the city of'}], 'dataBaseCol': ['PublicListingRemarks', 'PropertyConditionDetails', 'RepairsDetails', 'ConstructionMaterials', 'PetsDetails', 'SchoolElementary', 'SchoolMiddle', 'SchoolHigh']}, 'house': {'images': [{'image': 'photo_1.jpg', 'details': 'a white house with a driveway in front of it'}, {'image': 'photo_24.jpg', 'details': 'a white house with a tree in the yard'}, {'image': 'photo_28.jpg', 'details': 'a white house with a driveway in front of it'}, {'image': 'photo_29.jpg', 'details': 'a white house with flowers in front of it'}], 'dataBaseCol': ['MLSPropertyType', 'MLSListingAddress', 'Stories', 'LatestListingPrice', 'MarketValue', 'LotDimensions', 'LotFeatureList', 'LotSizeAcres', 'YearBuilt', 'RepairsYN', 'NewConstructionYN', 'ConstructionMaterials']}, 'kitchen': {'images': [{'image': 'photo_10.jpg', 'details': 'a kitchen with white cabinets and blue counter tops'}, {'image': 'photo_11.jpg', 'details': 'a kitchen with white cabinets and a refrigerator'}, {'image': 'photo_12.jpg', 'details': 'a kitchen with white cabinets and blue counter tops'}, {'image': 'photo_6.jpg', 'details': 'a kitchen with white cabinets and white appliances'}], 'dataBaseCol': ['AppliancesDetails', 'OtherEquipmentIncluded', 'GasDescriptionDetails', 'UtilitiesDetails', 'WaterSourceDetails']}, 'bath': {'images': [{'image': 'photo_14.jpg', 'details': 'a bathroom with a sink, toilet, and mirror'}, {'image': 'photo_18.jpg', 'details': 'a bathroom with a sink, toilet, and mirror'}, {'image': 'photo_19.jpg', 'details': 'a bathroom with a sink and mirror in it'}], 'dataBaseCol': ['BathroomsFull', 'BathroomsHalf', 'LaundryDetails']}, 'room': {'images': [{'image': 'photo_13.jpg', 'details': 'a room with a ceiling fan and a ceiling fan'}, {'image': 'photo_15.jpg', 'details': 'a room with a ceiling fan and a ceiling fan'}, {'image': 'photo_16.jpg', 'details': 'a room with a ceiling fan and tile floor'}, {'image': 'photo_17.jpg', 'details': 'a room with a ceiling fan and tile floor'}, {'image': 'photo_3.jpg', 'details': 'a room with a ceiling fan and a ceiling fan'}, {'image': 'photo_5.jpg', 'details': 'a room with a ceiling fan and a ceiling fan'}, {'image': 'photo_7.jpg', 'details': 'a room with white walls and beige tile flooring'}, {'image': 'photo_9.jpg', 'details': 'a room with a ceiling fan and a ceiling fan'}, {'image': 'photo_4.jpg', 'details': 'an empty living room with a ceiling fan'}], 'dataBaseCol': ['LivingAreaSquareFeet', 'RoomsTotal', 'InteriorDetails', 'RoofDetails', 'ArchitecturalStyleDetails', 'LivingAreaSource', 'CoolingDetails', 'HeatingDetails', 'FireplaceDetails', 'BasementDetails', 'BasementTotalSqFt', 'PropertyAttachedYN', 'SewerDetails']}, 'patio': {'images': [{'image': 'photo_8.jpg', 'details': 'a patio with a ceiling fan and a ceiling fan'}], 'dataBaseCol': ['ExteriorDetails', 'PatioAndPorchDetails']}, 'garage': {'images': [{'image': 'photo_20.jpg', 'details': 'a walk in closet with white walls and a white door'}, {'image': 'photo_25.jpg', 'details': 'a white fence in front of a house'}], 'dataBaseCol': ['ExteriorDetails', 'FencingDetails', 'LotSizeSquareFeet', 'LotFeatureList', 'GarageSpaces', 'GarageYN', 'AttachedGarageYN', 'OpenParkingSpaces', 'ParkingOther', 'CarportSpaces']}, 'view': {'images': [{'image': 'photo_22.jpg', 'details': 'an aerial view of a house from above'}, {'image': 'photo_26.jpg', 'details': 'an aerial view of a residential area in a residential neighborhood'}], 'dataBaseCol': ['ViewDetails', 'WaterfrontDetails', 'PatioAndPorchDetails', 'Topography']}}
        print('scenes_data->',self.scenes_data)
        scenes_arr=self.get_scenes_array(videoStructure)
        # scenes_arr = [{'dataBaseData': {'ViewDetails': '', 'WaterfrontDetails': '', 'PatioAndPorchDetails': '', 'Topography': ''}, 'images': [{'image': 'photo_22.jpg', 'details': 'an aerial view of a house from above', 'script': "From high above, you can see the stunning waterfront views this house offers. Let's dive into the details."}, {'image': 'photo_26.jpg', 'details': 'an aerial view of a residential area in a residential neighborhood'}], 'scene_type': 'view'}, {'dataBaseData': {'MLSPropertyType': 'residential', 'MLSListingAddress': '1412 Sw 19Th Place', 'Stories': 1, 'LatestListingPrice': ('314900.00'), 'MarketValue': ('268489.00'), 'LotDimensions': '80 x 120 x 80 x 120', 'LotFeatureList': 'RectangularLot', 'LotSizeAcres': ('0.23'), 'YearBuilt': 2002, 'RepairsYN': False, 'NewConstructionYN': False, 'ConstructionMaterials': 'block,concrete,stucco'}, 'images': [{'image': 'photo_1.jpg', 'details': 'a white house with a driveway in front of it', 'script': "Pulling up to this charming white house with a spacious driveway, let's explore what makes this property a must-see."}, {'image': 'photo_24.jpg', 'details': 'a white house with a tree in the yard'}, {'image': 'photo_28.jpg', 'details': 'a white house with a driveway in front of it'}, {'image': 'photo_29.jpg', 'details': 'a white house with flowers in front of it'}], 'scene_type': 'house'}, {'dataBaseData': {'LivingAreaSquareFeet': ('1287.00'), 'RoomsTotal': 0, 'InteriorDetails': 'breakfastbar,bedroomonmainlevel,familydiningroom,livingdiningroom,mainlevelprimary,tubshower,bar,splitbedrooms', 'RoofDetails': 'shingle', 'ArchitecturalStyleDetails': 'ranch,onestory', 'LivingAreaSource': 'appraiser', 'CoolingDetails': 'centralair,electric', 'HeatingDetails': 'central,electric', 'FireplaceDetails': '', 'BasementDetails': '', 'BasementTotalSqFt': ('0.00'), 'PropertyAttachedYN': False, 'SewerDetails': 'assessmentunpaid'}, 'images': [{'image': 'photo_13.jpg', 'details': 'a room with a ceiling fan and a ceiling fan', 'script': 'Step into this cozy room with a ceiling fan and discover the inviting features that make this house a perfect home.'}, {'image': 'photo_15.jpg', 'details': 'a room with a ceiling fan and a ceiling fan'}, {'image': 'photo_16.jpg', 'details': 'a room with a ceiling fan and tile floor'}, {'image': 'photo_17.jpg', 'details': 'a room with a ceiling fan and tile floor'}, {'image': 'photo_3.jpg', 'details': 'a room with a ceiling fan and a ceiling fan'}, {'image': 'photo_5.jpg', 'details': 'a room with a ceiling fan and a ceiling fan'}, {'image': 'photo_7.jpg', 'details': 'a room with white walls and beige tile flooring'}, {'image': 'photo_9.jpg', 'details': 'a room with a ceiling fan and a ceiling fan'}, {'image': 'photo_4.jpg', 'details': 'an empty living room with a ceiling fan'}], 'scene_type': 'room'}, {'dataBaseData': {'BathroomsFull': 2, 'BathroomsHalf': 0, 'LaundryDetails': 'inside'}, 'images': [{'image': 'photo_14.jpg', 'details': 'a bathroom with a sink, toilet, and mirror', 'script': 'Experience the serene bathroom with modern amenities – a perfect retreat within this beautiful home.'}, {'image': 'photo_18.jpg', 'details': 'a bathroom with a sink, toilet, and mirror'}, {'image': 'photo_19.jpg', 'details': 'a bathroom with a sink and mirror in it'}], 'scene_type': 'bath'}, {'dataBaseData': {'AppliancesDetails': 'dishwasher,freezer,microwave,range,refrigerator', 'OtherEquipmentIncluded': '', 'GasDescriptionDetails': '', 'UtilitiesDetails': 'cableavailable', 'WaterSourceDetails': 'assessmentunpaid'}, 'images': [{'image': 'photo_10.jpg', 'details': 'a kitchen with white cabinets and blue counter tops', 'script': 'Get ready to be wowed by this stylish kitchen with white cabinets and blue countertops, equipped with top-of-the-line appliances for your culinary adventures.'}, {'image': 'photo_11.jpg', 'details': 'a kitchen with white cabinets and a refrigerator'}, {'image': 'photo_12.jpg', 'details': 'a kitchen with white cabinets and blue counter tops'}, {'image': 'photo_6.jpg', 'details': 'a kitchen with white cabinets and white appliances'}], 'scene_type': 'kitchen'}]
        print("scenes_arr",scenes_arr)        

        self.construct_senses_parallel(scenes_arr, videoStructure)

        print('Starting Final Rendering',self.video)
        self.join_videos()

    def construct_intro(self,scene_type:str)->list:
        return Scene(scene_type,None,self.uuid,self.output_dir,self.frame_rate,self.scene_chunk_len).videos.copy()

    def construct_senses(self,scene_data:dict)->list:
        return Scene(scene_data['scene_type'],scene_data,self.uuid,self.output_dir,self.frame_rate,self.scene_chunk_len).videos.copy()

    def construct_senses_parallel(self, scenes_arr: list, videoStructure: list):
        self.video.extend(self.construct_intro('intro'))

        with ThreadPoolExecutor() as executor:
            results = [
                executor.submit(self.construct_senses, scene)
                for scene in scenes_arr if scene['scene_type'] in videoStructure
            ]
            
            for result in results:
                self.video.extend(result.result())

    def join_videos(self):
        # self.video = ['tmp\\00138401-77e9-4474-ae25-a53b2ec1f0c3/save/intro/intro1.mp4', 'tmp\\00138401-77e9-4474-ae25-a53b2ec1f0c3/save/intro/intro2.mp4', 'tmp\\00138401-77e9-4474-ae25-a53b2ec1f0c3/save/garage//photo_47.mp4', 'tmp\\00138401-77e9-4474-ae25-a53b2ec1f0c3/save/garage//photo_50.mp4', 'tmp\\00138401-77e9-4474-ae25-a53b2ec1f0c3/save/patio//photo_14.mp4', 'tmp\\00138401-77e9-4474-ae25-a53b2ec1f0c3/save/patio//photo_15.mp4', 'tmp\\00138401-77e9-4474-ae25-a53b2ec1f0c3/save/bath//photo_29.mp4', 'tmp\\00138401-77e9-4474-ae25-a53b2ec1f0c3/save/bath//photo_30.mp4', 'tmp\\00138401-77e9-4474-ae25-a53b2ec1f0c3/save/room//photo_16.mp4', 'tmp\\00138401-77e9-4474-ae25-a53b2ec1f0c3/save/room//photo_17.mp4', 'tmp\\00138401-77e9-4474-ae25-a53b2ec1f0c3/save/bed//photo_27.mp4', 'tmp\\00138401-77e9-4474-ae25-a53b2ec1f0c3/save/bed//photo_28.mp4', 'tmp\\00138401-77e9-4474-ae25-a53b2ec1f0c3/save/kitchen//photo_18.mp4', 'tmp\\00138401-77e9-4474-ae25-a53b2ec1f0c3/save/kitchen//photo_19.mp4', 'tmp\\00138401-77e9-4474-ae25-a53b2ec1f0c3/save/house//photo_1.mp4', 'tmp\\00138401-77e9-4474-ae25-a53b2ec1f0c3/save/house//photo_2.mp4', 'tmp\\00138401-77e9-4474-ae25-a53b2ec1f0c3/save/view//photo_10.mp4', 'tmp\\00138401-77e9-4474-ae25-a53b2ec1f0c3/save/view//photo_12.mp4']
        print('Video_Arr->',self.video)
        self.reorder_videos(self.video)
        video_clips = [VideoFileClip(video_path) for video_path in self.video]
        final_video = concatenate_videoclips(video_clips,method='compose')
        output_video_path = os.path.join(self.output_dir, f'{self.uuid}/save/final_video.mp4')
        self.final_video_save_dir= output_video_path
        final_video.write_videofile(output_video_path, fps=self.frame_rate)

        # Close the video clips to release resources
        for clip in video_clips:
            clip.close()

    def reorder_videos(self,video_paths:list):
        desired_order = ['intro', 'view', 'house', 'room', 'bed', 'bath', 'kitchen', 'patio', 'pool', 'garage', 'outro']
        self.video = sorted(video_paths, key=lambda x: [desired_order.index(folder) for folder in desired_order if folder in x])



    # --------------------------------------PreProcessing & Downloading Images----------------------------------------
    def check_and_resize_image(self,image_content, target_width=1920, target_height=1080):
        # Check if the aspect ratio is within the desired range
        image = Image.open(BytesIO(image_content))
        width, height = image.size 
        aspect_ratio = width / height

        if 1.2 < aspect_ratio < 2.2:
            return  image.resize((target_width, target_height), Image.Resampling.LANCZOS)
        else:
            return None
  
    def download_single_image(self, urls_and_filenames):
        url, filename = urls_and_filenames
        try:
            response = requests.get(url)
            response.raise_for_status()

            # Get the original image format
            image = Image.open(BytesIO(response.content))
            resized_image = self.check_and_resize_image(response.content)
            
            if resized_image:
                # Convert to JPG if it's not already a JPG
                if image.format != 'JPEG':
                    filename = os.path.splitext(filename)[0] + '.jpg'
                    resized_image = resized_image.convert("RGB")  # Convert to RGB as JPG doesn't support transparency
                resized_image.save(filename, 'JPEG')
            
        except requests.exceptions.HTTPError as err:
            print(f"Failed to download {url}: {err}")
            
        except Exception as e:
            print(f"An error occurred: {e}")  

    def download_images_from_uuid(self)->bool:
        cursor =None
        try:
            cursor = self.conn.cursor()
            query = """SELECT "PhotoURLPrefix", "PhotoKey", "PhotosCount" FROM properties_property WHERE "PropertyID" = %s;"""
            cursor.execute(query, (self.uuid,))
            result = cursor.fetchone()
            if result:
                prefix, key, count = result
                dir = f'{self.output_dir}/{self.uuid}'
                os.makedirs(dir, exist_ok=True)

                urls_and_filenames = []
                for i in range(1, count + 1):
                    url = f"{prefix}{key}/photo_{i}.jpg"
                    filename = f"{dir}/photo_{i}.jpg"
                    urls_and_filenames.append((url, filename))

                with ThreadPoolExecutor() as executor:
                    executor.map(self.download_single_image, urls_and_filenames)

                return True
            else:
                print(f"No data found for UUID: {self.uuid}")
                return False
        
        except Exception as e:
            print(f"An error occurred: {e}")
            return False
        finally:    
            cursor.close()        
    
    def download_and_caption_images(self, batch_size=25):
        image_captions = {}

        # Download images
        if not self.download_images_from_uuid():
            return image_captions
        
        # Get list of all image files
        file_list = self.get_all_files_in_folder(f"{self.output_dir}/{self.uuid}/")
        print('Downloaded and preporcessed Images')
        # Load the caption model components
        nlp, processor, model = self.load_caption_model()
        print('Loaded Model')

        # Helper function to batch the files into chunks
        def batch(iterable, n=1):
            iterable_len = len(iterable)
            for ndx in range(0, iterable_len, n):
                yield iterable[ndx:min(ndx + n, iterable_len)]

        # Process the files in batches
        with ThreadPoolExecutor() as executor:
            # Create batches of size `batch_size`
            batches = list(batch(file_list, batch_size))
            
            # Submit batches for parallel processing
            for batch_files in batches:
                results = list(executor.map(lambda file: self.process_image(file, model, processor, nlp), batch_files))

                # Collect results from the processed images
                for file, caption, details in results:
                    if caption in image_captions:
                        image_captions[caption].append({'image': file, 'details': details})
                    else:
                        image_captions[caption] = [{'image': file, 'details': details}]
        
       
        return image_captions


    # --------------------------------------Caption Images & Make Structured Json----------------------------------------
    def load_caption_model(self):
        nlp = spacy.load("en_core_web_sm")
        processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
        model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")
        return nlp,processor,model

    def image_caption(self,image_path:str, model:BlipForConditionalGeneration, processor:BlipProcessor, nlp:spacy):
        image = Image.open(image_path)
        # Generate caption
        inputs = processor(images=image, return_tensors="pt")
        output = model.generate(**inputs, max_length=15, num_beams=3, repetition_penalty=1.0, length_penalty=1.0)
        caption = processor.decode(output[0], skip_special_tokens=True)
        # Extract the main noun phrase as the room name using spaCy
        doc = nlp(caption)
        room_names = [chunk.text for chunk in doc.noun_chunks]
        noun = room_names[0].replace(' ', '_') if room_names else "Unknown"
        return noun, caption

    def get_all_files_in_folder(self,folder_path:str)->list:
        files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
        return files

    def process_image(self,file:str, model:BlipForConditionalGeneration, processor:BlipProcessor, nlp:spacy):
        image_path = os.path.join(self.output_dir, self.uuid, file)
        caption,details = self.image_caption(image_path, model, processor, nlp)
        return file, caption, details

    def find_matching_keys(self,json_data: dict, search_string: str): 
        matched_keys_and_contents = []
        for key, contents in json_data.items(): 
            if search_string.lower() in key.lower():
                # Append the matched key and its contents to the list
                matched_keys_and_contents.append((key, contents))
        return matched_keys_and_contents

    def get_scene_info(self,captioned_images:dict,)->dict:
        scene_json = {
            'outro': {
                'images': [],
                'dataBaseCol': ['PublicListingRemarks','PropertyConditionDetails','RepairsDetails','ConstructionMaterials','PetsDetails','SchoolElementary','SchoolMiddle','SchoolHigh'],
            }
        }
        scene_mapping = {
            'house':{'tags':['house','home','front','cottage','condo','apartment','residence'], "dataBaseCol":['MLSPropertyType','MLSListingAddress','Stories','LatestListingPrice','MarketValue','LotDimensions','LotFeatureList','LotSizeAcres','YearBuilt','RepairsYN','NewConstructionYN','ConstructionMaterials']},
            'bed':  {'tags':['bed','bed_room'], "dataBaseCol":['BedroomsTotal']},
            'kitchen':{'tags':['kitchen','cooking'], "dataBaseCol":['AppliancesDetails','OtherEquipmentIncluded','GasDescriptionDetails','UtilitiesDetails','WaterSourceDetails']},
            'bath': {'tags':['bath','bath_room','toothbrush','laundry','toilet','sink','shower','spa'], "dataBaseCol":['BathroomsFull', 'BathroomsHalf', 'LaundryDetails']},
            'room': {'tags':['room','living','dining','hallway'], "dataBaseCol": ['LivingAreaSquareFeet','RoomsTotal','InteriorDetails','RoofDetails','ArchitecturalStyleDetails','LivingAreaSource','CoolingDetails','HeatingDetails','FireplaceDetails','BasementDetails','BasementTotalSqFt','PropertyAttachedYN','SewerDetails']},
            'patio': {'tags':['patio','balcony','porch','terrace','rooftop'], "dataBaseCol": ['ExteriorDetails','PatioAndPorchDetails']},
            'pool':{'tags':['pool','swimming'], "dataBaseCol": ['PoolPrivateYN', 'PoolDetails']},
            'garage':{'tags':['garage','shed','garden','lawn','barn','workshop','land','driveway','exterior','yard','fenc','field','ground','walk','parking','carport'], "dataBaseCol": ['ExteriorDetails','FencingDetails','LotSizeSquareFeet', 'LotFeatureList','GarageSpaces','GarageYN','AttachedGarageYN','OpenParkingSpaces','ParkingOther','CarportSpaces']},
            'view': {'tags':['view','tree','flower','sand','ocean','sea','beach','mountain','road','sky','area','picnic','terrain','environment','horizon','scene','sun'], "dataBaseCol":['ViewDetails','WaterfrontDetails','PatioAndPorchDetails','Topography']},}
         
        scenes_to_check = list(captioned_images.keys())

        for key, value in scene_mapping.items():
            tags = value['tags']
            matched_images = []

            for scene in scenes_to_check:
                # Check if the scene exists in captioned_images
                if scene in captioned_images:
                    images = captioned_images[scene]

                    # Check if any tag matches the scene
                    if any(tag in scene for tag in tags):
                        matched_images.extend(images)

            if matched_images:
                scene_json[key] = {'images': matched_images, 'dataBaseCol': value['dataBaseCol']}
                for scene in list(captioned_images.keys()):
                    if any(tag in scene for tag in tags):
                        captioned_images.pop(scene)

        remaining_images = []
        for scene in captioned_images:
            remaining_images.extend(captioned_images[scene])
        
        scene_json['outro']['images'] = remaining_images
        return scene_json 

    def construct_senses_json(self)->dict:
        captioned_images = self.download_and_caption_images()
        if captioned_images:
            return self.get_scene_info(captioned_images.copy())
        else:
            return {}
        
    def get_scene_data_from_db(self,scene_type:str)->dict:
        val={}
        result={}
        scene_data = self.scenes_data[scene_type]

        columns = scene_data['dataBaseCol']
        columns_str = ', '.join([f'"{col}"' for col in columns])
        query = f"""SELECT {columns_str} FROM properties_property WHERE "PropertyID" = %s"""

        try:
            cur = self.conn.cursor()
            cur.execute(query, (self.uuid,))
            data = cur.fetchone()
            
            if data:
                val = dict(zip(columns, data))
                result  = {'dataBaseData':val,'images':scene_data['images'],'scene_type':scene_type}
                for image_obj in result['images'][:self.scene_chunk_len]:
                    details = image_obj.get('details')
                    image_obj['script'] = self.get_image_script(scene_type, details, scene_data['dataBaseCol'])
            else:
                print(f"No data or connection: {self.uuid}")

        except Exception as e:
            print(f"An error occurred: {e}")
        
        finally:
            cur.close()
            return result
    
    def get_scenes_array(self,videoStructure:list):
        if not self.scenes_data:
            return "Unabel to Create Video"
        print('writing scenes scripts')
        scenes_arr=[]
        for scene in videoStructure:
            if scene in self.scenes_data:
                scenes_arr.append(self.get_scene_data_from_db(scene))
        
        return scenes_arr
            

    # -------------------------------------GPT functions-----------------------------------------
    def make_user_message(self,type:str,image_detail:str,db:str)->str:
        return f'''scene_type":{type},"image_caption":{image_detail}, database_results:{db}'''

    def get_image_script(self,type:str,image_detail:str,db:str)->str:
        try:
            msg = self.make_user_message(type,image_detail,db)
            scriptWriter = AgentsHub().getscriptWriter()
            response = executeBasicAgent(scriptWriter, self.threadId, msg)
            return response
        except Exception as e:
            print(f"An error occurred get_image_script: {e}")