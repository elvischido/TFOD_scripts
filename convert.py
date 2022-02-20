import json
from PIL import Image
import os
import shutil
import argparse

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'    # Suppress TensorFlow logging (1)


# Initiate argument parser
parser = argparse.ArgumentParser(
    description="Script to convert Malaria Dataset annotation to pascal voc")
parser.add_argument("-id",
                    "--img_dir",
                    help="Path to the folder where the the img files and annotations are stored.",
                    type=str)
parser.add_argument("-dd",
                    "--data_dir",
                    help="Path to the folder where the the compressed files are stored.", type=str)
parser.add_argument("-cw",
                    "--cls_wts",
                    help="a string containing the class weights.", type=str)
parser.add_argument("-cm",
                    "--cls_mp",
                    help="a .json file containing classes to be mapped",
                    type=str, default=None)

args = parser.parse_args()

directory = args.img_dir
data_directory = args.data_dir
class_weights = json.loads(args.cls_wts)
class_maps = json.loads(args.cls_mp)

#print (directory)
#print (data_directory)
#print (class_weights)
#print (class_maps)

try:
    #os.mkdir(directory+'/labels/')
    os.mkdir(directory)
except OSError as error:
    print(error)

try:
    os.mkdir(directory +'/training/')
except OSError as error:
    print(error)

try:
    os.mkdir(directory + '/test/')
except OSError as error:
    print(error)

def wt_frm_name(name):
  wt = class_weights[name]
  return wt

def map_frm_name(name):
  wt = class_maps[name]
  return wt

for mode in ['training', 'test']:
    inf_ct = 0
    uninf_ct = 0
    rmv = 0
    no_of_files = 0
    with open (data_directory + "/{}.json".format(mode), "r") as myfile:
        data = json.loads(myfile.read())
        for sample in data:
            image_src = data_directory + sample['image']['pathname']
            #img_dir = directory + '/labels/{}'.format(mode)
            img_dir = directory + '/' + '{}'.format(mode)
            image = Image.open(image_src)
            width, height = image.size
            
            no_of_files += 1 # count the number of images
            
            #print(image_src)
            #print(img_dir + sample['image']['pathname'])
            
            shutil.copyfile(image_src, img_dir + '/' + sample['image']['pathname'].split('/')[-1])


            filename = sample['image']['pathname'].split('/')[-1]
            path = '..' + sample['image']['pathname']

            output = "<annotation>\n\t<folder>malaria</folder>"
            output += "\n\t<filename>{}</filename>\n\t<path>{}</path>".format(filename, path)
            output += "\n\t<size>\n\t\t<width>{}</width>\n\t\t<height>{}</height>".format(width, height)
            output += "\n\t\t<depth>3</depth>\n\t</size>\n\t<segmented>0</segmented>"

            for object in sample['objects']:
                category = map_frm_name(object['category'])
                #print(category)
                xmin = object['bounding_box']['minimum']['c']
                ymin = object['bounding_box']['minimum']['r']
                xmax = object['bounding_box']['maximum']['c']
                ymax = object['bounding_box']['maximum']['r']

                #https://stackoverflow.com/questions/51862997/class-weights-for-balancing-data-in-tensorflow-object-detection-api
                if category == 'infected': 
                  inf_ct += 1
                if category == 'uninfected':
                  uninf_ct += 1
                if category == 'rmv':
                  rmv += 1
                if category != 'rmv': # take out rbcs from annotation
                  output += "\n\t<object>\n\t\t<name>{}</name>\n\t\t<pose>Unspecified</pose>".format(category)
                
                  output += "\n\t\t<truncated>0</truncated>\n\t\t<difficult>0</difficult>\n\t\t<bndbox>"
                  output += "\n\t\t\t<xmin>{}</xmin>\n\t\t\t<ymin>{}</ymin>".format(xmin, ymin)
                  output += "\n\t\t\t<xmax>{}</xmax>\n\t\t\t<ymax>{}</ymax>".format(xmax, ymax)
                  output += "\n\t\t</bndbox>"
                  output += "\n\t\t<weight>{}</weight>".format(wt_frm_name(category)) # to add class weights to annotation https://stackoverflow.com/questions/51862997/class-weights-for-balancing-data-in-tensorflow-object-detection-api
                  output += "\n\t</object>"

            output += "\n</annotation>"

            with open(directory + "/{}/{}.xml".format(mode, sample['image']['pathname'].split('/')[-1].split('.')[0]), "w") as myfile:
                myfile.write(output)

    print ("{} dataset created with {} files containing {} uninfected cells, {} infected cells. {} cells were removed.".format(no_of_files, mode, uninf_ct, inf_ct, rmv))
