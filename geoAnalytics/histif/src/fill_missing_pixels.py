import numpy as np
from sklearn.neighbors import KDTree


def fill_pixels(input_frame, neighbors = 4):
    """
    Fill the missing pixels in the input frame.
    Args:
        input_frame (_numpy_array_): _The input frame is the numpy array containing pixels_
        neighbors (int, optional): _Number of neighbors to consider for imputing_. Defaults to 4.

    Returns:
        _numpy_array_: _The frame after imputing missing pixels._
    """
    image_frame = np.copy(input_frame)
    temp_frame = np.isnan(image_frame)
    missing_pixels = np.argwhere(temp_frame == True)

    if(len(missing_pixels) == 0):
        return image_frame
    
    pixels_frame = np.argwhere(temp_frame == False)
    tree = KDTree(pixels_frame, leaf_size = 2)
    dist, ind = tree.query(missing_pixels, k = neighbors)
    for i in range(len(missing_pixels)):
        nearest_pixels = ind[i]
        weighted_sum = 0
        for j in range(neighbors):
            weighted_sum += (dist[j] * image_frame[pixels_frame[nearest_pixels[j]][0]][pixels_frame[nearest_pixels[j]][1]])
            
        image_frame[missing_pixels[i]] = weighted_sum / sum(list(dist))
    
    return image_frame