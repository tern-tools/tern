import os
import yaml
'''
Docker image and layer related modules
'''

# known layer database
layer_db_file = 'layer_db.yml'
layer_db = {}
with open(os.path.abspath(layer_db_file)) as f:
    layer_db = yaml.safe_load(f)


def check_trusted(image, tag='latest'):
    '''Check to see if the given image is trusted
    Return a string: 'image:tag'
    Else raise a NameError
    WARNING: if a Dockerfile does not specify a tag, Docker will pull down
    the tag marked 'latest'. The list of trusted images should be kept up to
    date on the tag 'latest' is pointing to. We assume that the images
    being produced from the Dockerfile pulling from the 'latest' tag are
    taken care of by the maintainer of the images'''
    ret_string = ''
    # list of trusted images
    images = trusted.keys()
    if image in images:
        # list of trusted tags
        if tag == 'latest':
            ret_string = image + ':' + trusted[image]['latest']
        elif tag in trusted[image]['tags']:
            ret_string = image + ':' + tag
        else:
            raise NameError('Not a trusted Docker tag for image: ' + image)
    else:
        raise NameError('Not a trusted Docker image: ' + image)
    return ret_string
