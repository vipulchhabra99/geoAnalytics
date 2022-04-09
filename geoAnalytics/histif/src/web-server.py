import re
from flask import Flask, render_template, request, current_app, send_from_directory, send_file
from werkzeug.utils import secure_filename
from main_psf import main_psf
from matplotlib import pyplot as plt
import numpy as np
import global_vars
import gdal
import uuid
import os
import shutil
from evaluation import *


app = Flask(__name__)

@app.route('/')
def upload_file():
   return render_template('upload.html')

@app.route('/uploads/<path:filename>', methods=['GET', 'POST'])
def download(filename):
    uploads = f'static/results/{filename}'
    return send_file(uploads, as_attachment=True)
	
@app.route('/uploader', methods = ['GET', 'POST'])
def upload():
   if request.method == 'POST':
      temp_folder = str(uuid.uuid4())
      temp_path = os.path.join('tmp', temp_folder)
      print(temp_path)
      os.mkdir(temp_path)

      f = request.files['fine_file0']
      c_f = request.files['coarse_file0']
      c_f2 = request.files['coarse_file1']
      f_1_path = None
      try:
         if('fine_file1' in request.files):
            f_1 = request.files['fine_file1']
            f_1.save(os.path.join(temp_path, secure_filename(f_1.filename)))
            f_1_path = os.path.join(temp_path, f_1.filename)


      except:
         pass

      f.save(os.path.join(temp_path, secure_filename(f.filename)))
      c_f.save(os.path.join(temp_path, secure_filename(c_f.filename)))
      c_f2.save(os.path.join(temp_path, secure_filename(c_f2.filename)))
      # print(request)
      fmwh_x1 = float(request.form['fwmhx_start'])
      fmwh_x2 = float(request.form['fwmhx_end'])
      fmwh_y1 = float(request.form['fwmhy_start'])
      fmwh_y2 = float(request.form['fwmhy_end'])
      shiftx_start = float(request.form['shiftx_start'])
      shiftx_end = float(request.form['shiftx_end'])
      shifty_start = float(request.form['shifty_start'])
      shifty_end = float(request.form['shifty_end'])
      rot_angle_f = float(request.form['rot_start'])
      rot_angle_e = float(request.form['rot_end'])
      iterations = int(request.form['iters'])
      neighbors = int(request.form['neighbors'])

      c_f_path = os.path.join(temp_path, c_f.filename)
      f_path = os.path.join(temp_path, f.filename)
      c_f2_path = os.path.join(temp_path, c_f2.filename)
      
      params = np.array([[fmwh_x1, fmwh_x2], [fmwh_y1, fmwh_y2], [shiftx_start, shiftx_end], [shifty_start, shifty_end], [rot_angle_f, rot_angle_e]])
      img_data_new, final_img = main_psf(c_f_path, f_path, c_f2_path, params, iterations, 0, neighbors = neighbors)

      dst_filename = str(uuid.uuid4())
      x_pixels = (final_img[0]).shape[0]  # number of pixels in x
      y_pixels = (final_img[0]).shape[1]  # number of pixels in y
      driver = gdal.GetDriverByName('GTiff')
      print(len(final_img))
      dataset = driver.Create(f'static/results/{dst_filename}.tif',x_pixels, y_pixels, len(final_img),gdal.GDT_Float32)
      for band_range in range(len(final_img)):
         dataset.GetRasterBand(band_range+1).WriteArray(final_img[band_range])
      data0 = gdal.Open(f_path)
      geotrans=data0.GetGeoTransform()
      proj=data0.GetProjection()
      dataset.SetGeoTransform(geotrans)
      dataset.SetProjection(proj)
      dataset.FlushCache()
      dataset=None

      global_vars.pre_image = None
      cc = None
      rmse = None
      mabs = None

      if(f_1_path is not None):
         result_path = f'static/results/{dst_filename}.tif'
         cc = find_cc(f_1_path, result_path)
         rmse = find_rmse(f_1_path, result_path)
         mabs = find_mean_absolute_difference(f_1_path, result_path)

         for i in range(len(cc)):
            cc[i] = round(cc[i], 4)
            rmse[i] = round(rmse[i], 4)
            mabs[i] = round(mabs[i], 4)

      shutil.rmtree(temp_path)
      return render_template('plot.html', url='/static/images/plot.png', download_link = f"/uploads/{dst_filename}.tif", cc = cc, rmse = rmse, mabs = mabs)
		
if __name__ == '__main__':
   app.run(debug = True)