'''
Functions specific to Docker FROM
'''
import yaml

# trusted images dictionary
trusted_file = 'trusted_base.yml'
trusted = {}
with open(trusted_file) as f:
    trusted = yaml.safe_load(f)


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


def parse_image_tag(from_string):
    '''Given the predicate of Docker FROM directive, return a tuple
    containing the image and tag'''
    image = ''
    tag = 'latest'
    image_tag_list = from_string.split(':')
    image = image_tag_list[0].strip()
    if len(image_tag_list) != 1:
        # there is a tag
        tag = image_tag_list[1].strip()
    return (image, tag)
