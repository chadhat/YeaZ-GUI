# Run:
#
# python Launch_NN_command_line.py -i DIRECTORY/IMAGE_FILE -m OUTPUT_MASK_FILE --path_to_weights PATH_TO_HDF5_FILE --fov N --range_of_frames n1 n2 --min_seed_dist 5 --threshold 0.5
# 
# or:
#
# python Launch_NN_command_line.py -i DIRECTORY/IMAGE_FILE -m OUTPUT_MASK_FILE --image_type pc_OR_bf               --fov N --range_of_frames n1 n2 --min_seed_dist 5 --threshold 0.5


import sys
sys.path.append("./unet")
sys.path.append("./disk")

#Import all the other python files
#this file handles the interaction with the disk, so loading/saving images
#and masks and it also runs the neural network.

from GUI_main import App
from segment import segment
import Reader as nd
import argparse
import skimage
import neural_network as nn


def LaunchInstanceSegmentation(reader, image_type, fov_indices=[0], time_value1=0, time_value2=0, thr_val=None, min_seed_dist=5, path_to_weights=None):
    """
    """

    # cannot have both path_to_weights and image_type supplied
    if (image_type is not None) and (path_to_weights is not None):
        print("image_type and path_to_weights cannot be both supplied.")
        return
    

    # check if correct imaging value
    if (image_type not in ['bf', 'pc']) and (path_to_weights is None):
        print("Wrong imaging type value ('{}')!".format(image_type),
              "imaging type must be either 'bf' or 'pc'")
        return
    is_pc = image_type == 'pc'

    # check range_of_frames constraint
    if time_value1 > time_value2 :
        print("Error", 'Invalid Time Constraints')
        return
    
    # displays that the neural network is running
    print('Running the neural network...')
    
    for fov_ind in fov_indices:

        #iterates over the time indices in the range
        for t in range(time_value1, time_value2+1):         
            print('--------- Segmenting field of view:',fov_ind,'Time point:',t)

            #calls the neural network for time t and selected fov
            im = reader.LoadOneImage(t, fov_ind)

            try:
                pred = App.LaunchPrediction(im, is_pc, pretrained_weights=path_to_weights)
            except ValueError:
                print('Error! ',
                      'The neural network weight files could not '
                      'be found. \nMake sure to download them from '
                      'the link in the readme and put them into '
                      'the folder unet, or specify a path to a custom weights file with -w argument.')
                return

            thresh = App.ThresholdPred(thr_val, pred)
            seg = segment(thresh, pred, min_seed_dist)
            reader.SaveMask(t, fov_ind, seg)
            print('--------- Finished segmenting.')
            
            # apply tracker if wanted and if not at first time
            temp_mask = reader.CellCorrespondence(t, fov_ind)
            reader.SaveMask(t, fov_ind, temp_mask)

def main(args):

    if '.h5' in args.mask_path:
        args.mask_path = args.mask_path.replace('.h5','')

    reader = nd.Reader("", args.mask_path, args.image_path)

    LaunchInstanceSegmentation(reader, args.image_type, args.fov,
                               args.range_of_frames[0],  args.range_of_frames[1], args.threshold, args.min_seed_dist, args.path_to_weights)

if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(description='', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-i', '--image_path', type=str, help="Specify the path to a single image or to a folder of images", required=True)
    parser.add_argument('-m', '--mask_path', type=str, help="Specify where to save predicted masks", required=True)
    parser.add_argument('--image_type', type=str, help="Specify the imaging type, possible 'bf' and 'pc'. Supersedes path_to_weights.")
    parser.add_argument('--path_to_weights', default=None, type=str, help="Specify weights path.")
    parser.add_argument('--fov', default=[0], nargs='+', type=int, help="Specify field of view index.")
    parser.add_argument('--range_of_frames', nargs=2, default=[0,0], type=int, help="Specify start and end in range of frames.")
    parser.add_argument('--threshold', default=None, type=float, help="Specify threshold value.")
    parser.add_argument('--min_seed_dist', default=5, type=int, help="Specify minimum distance between seeds.")
    args = parser.parse_args()
    main(args)
