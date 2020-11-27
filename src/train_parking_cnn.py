import math
import numpy as np
import re
import os
import subprocess

from collections import Counter
from matplotlib import pyplot as plt
from PIL import Image
import cv2

from keras import layers
from keras import models
from keras import optimizers

from keras.utils import plot_model
from keras import backend

#This training CNN model is from our enph 353 lab 5

def files_in_folder(folder_path):
  '''
  Returns a list of strings where each entry is a file in the folder_path.
  
  Parameters
  ----------
  
  folder_path : str
     A string to folder for which the file listing is returned.
     
  '''
#   command = "ls " + folder_path
#   files_A = os.system(command)
  files_A = os.listdir(folder_path)
  # The files when listed from Google Drive have a particular format. They are
  # grouped in sets of 4 and have spaces and tabs as delimiters.
  
  # Split the string listing sets of 4 files by tab and space and remove any 
  # empty splits.
  files_B = [list(filter(None, re.split('\t|\s', files))) for files in files_A]
  
  # Concatenate all splits into a single sorted list
  files_C = []
  for element in files_B:
    files_C = files_C + element
  files_C.sort()
  
  return files_C

action = 0

while action !=-1:
    action = input("Options: \n 1:load images \n 2: train cnn \n 3: see training history \n 4: test \n 5:save \n 6: reset \n -1: terminate \n input action:")

    #1: Load the pictures
    if (action == 1):
        PATH = "/home/fizzer/ros_ws/src/enph353_robot_controller/reader_utils/pictures/"
        # command = "ls " + PATH
        # labels_raw = os.system(command)
        labels_raw = os.listdir(PATH)
        labels = labels_raw[0].split()
        print(labels)

        folder_characters = PATH + "parking"
        char_files = files_in_folder(folder_characters)

        #assign integer encode,  ref: https://machinelearningmastery.com/how-to-one-hot-encode-sequence-data-in-python/
        ordered_data = '123456789'

        #define mapping of characters to integers
        char_to_int = dict((c,i) for i,c in enumerate(ordered_data))
        int_to_char = dict((i,c) for i,c in enumerate(ordered_data))


        #load the images and assign labels
        imgset_list =[]
        for file in char_files:
            ind_img = [cv2.imread('{}/{}'.format(folder_characters, file)), int(file[3])]
            imgset_list.append(ind_img)

        #imgset_list = [[np.array(Image.open('{}/{}'.format(folder_characters, file)), char_to_int[file[6]]] for file in char_files]
        imgset_chars = np.array(imgset_list)
        print("Loaded {:} images from folder:\n{}".format(imgset_chars.shape[0], folder_characters))

        # Genereate X and Y datasets
        X_dataset_orig = np.array([data[0] for data in imgset_chars])
        Y_dataset_orig = np.array([[data[1]] for data in imgset_chars]).T
        print(Y_dataset_orig)

        NUMBER_OF_LABELS = 9
        CONFIDENCE_THRESHOLD = 0.01

        def convert_to_one_hot(Y, C):
            Y = np.eye(C)[Y.reshape(-1)].T
            return Y

        # Normalize X (images) dataset
        X_dataset = X_dataset_orig/255.

        # Convert Y dataset to one-hot encoding
        Y_dataset = convert_to_one_hot(Y_dataset_orig, NUMBER_OF_LABELS).T
        print(Y_dataset[1])

        #split the data into training and test samples
        VALIDATION_SPLIT = 0.2
        print("Total examples: {}\nTraining examples: {}\nTest examples: {}".
            format(X_dataset.shape[0],
                    math.ceil(X_dataset.shape[0] * (1-VALIDATION_SPLIT)),
                    math.floor(X_dataset.shape[0] * VALIDATION_SPLIT)))
        print("X shape: " + str(X_dataset.shape))
        print("Y shape: " + str(Y_dataset.shape))
    
    # 2: train the CNN
    elif(action == 2):
        #Defining the model
        conv_model = models.Sequential()
        conv_model.add(layers.Conv2D(32, (3, 3), activation='relu',
                                    input_shape=(200, 100, 3)))
        conv_model.add(layers.MaxPooling2D((2, 2)))
        conv_model.add(layers.Conv2D(64, (3, 3), activation='relu',
                                    input_shape=(200, 100, 3)))
        conv_model.add(layers.MaxPooling2D((2, 2)))
        conv_model.add(layers.Flatten())
        conv_model.add(layers.Dropout(0.5))
        conv_model.add(layers.Dense(512, activation='relu'))
        conv_model.add(layers.Dense(9, activation='softmax'))
        conv_model.summary()

        #training the CNN
        LEARNING_RATE = 1e-4
        conv_model.compile(loss='categorical_crossentropy',
                        optimizer=optimizers.RMSprop(lr=LEARNING_RATE),
                        metrics=['acc'])
        history_conv = conv_model.fit(X_dataset, Y_dataset, 
                                    validation_split=VALIDATION_SPLIT, 
                                    epochs=10, 
                                    batch_size=16)

    # 3: See training history
    elif(action == 3):
        plt.plot(history_conv.history['loss'])
        plt.plot(history_conv.history['val_loss'])
        plt.title('model loss')
        plt.ylabel('loss')
        plt.xlabel('epoch')
        plt.legend(['train loss', 'val loss'], loc='upper left')
        plt.show()

        plt.plot(history_conv.history['acc'])
        plt.plot(history_conv.history['val_acc'])
        plt.title('model accuracy')
        plt.ylabel('accuracy (%)')
        plt.xlabel('epoch')
        plt.legend(['train accuracy', 'val accuracy'], loc='upper left')
        plt.show()

    # 4: Testing the model
    elif(action == 4):
       print("code not yet made")

    # 5: save the model
    elif(action == 5):
        conv_model.save("/home/fizzer/ros_ws/src/enph353_robot_controller/my_parking_reader")

    # 6: reset the model
    elif(action == 6):
        # Source: https://stackoverflow.com/questions/63435679
        def reset_weights(model):
            for ix, layer in enumerate(model.layers):
                if (hasattr(model.layers[ix], 'kernel_initializer') and 
                    hasattr(model.layers[ix], 'bias_initializer')):
                    weight_initializer = model.layers[ix].kernel_initializer
                    bias_initializer = model.layers[ix].bias_initializer

                    old_weights, old_biases = model.layers[ix].get_weights()

                    model.layers[ix].set_weights([
                        weight_initializer(shape=old_weights.shape),
                        bias_initializer(shape=len(old_biases))])

        reset_weights(conv_model)   
