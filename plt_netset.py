import numpy as np
import PIL
from PIL import Image
bands = ['theta', 'alpha', 'low_beta', 'high_beta', 'gamma']
fn_out = 'bands.jpg' 
list_ims = []
for band in bands:
    list_im = ['%s_icon_con.jpg' %band, 'incon_con_%s.jpg' %band]
    list_ims.append(list_im)
#list_im2 = ['RL_%s.jpg' %band, 'LR_%s.jpg' %band]
#list_im1 = sorted(list_im1)
#list_im2 = sorted(list_im2)
##list_im1 = glob.glob(imgs_dir + '/lh*.jpg')
##list_im2 = glob.glob(imgs_dir + '/rh*.jpg')
#list_ims = [list_im1, list_im2]

#list_im = ['Test1.jpg', 'Test2.jpg', 'Test3.jpg']
imgs_combs = []
for list_im in list_ims:
    images = map(Image.open, list_im)
    widths, heights = zip(*(i.size for i in images))

    total_width = sum(widths)
    max_height = max(heights)

    new_im = Image.new('RGB', (total_width, max_height))

    x_offset = 0
    for im in images:
        new_im.paste(im, (x_offset,0))
        x_offset += im.size[0]

    imgs_combs.append(new_im)
#imgs_comb.save( 'Trifecta.jpg' )    

# for a vertical stacking it is simple: use vstack
min_shape = sorted( [(np.sum(i.size), i.size ) for i in imgs_combs])[0][1]
imgs_sum = np.vstack( (np.asarray( i.resize(min_shape) ) for i in imgs_combs ) )
imgs_sum = PIL.Image.fromarray(imgs_sum)
imgs_sum.save(fn_out)
