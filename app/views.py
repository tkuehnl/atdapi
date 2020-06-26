from app import app

from flask import render_template
from flask import request, redirect, url_for, send_from_directory, jsonify
from zipfile import ZipFile
import os
from os.path import basename

from OCC.Extend.DataExchange import read_step_file
from OCC.Core.Tesselator import ShapeTesselator
from OCC.Extend.TopologyUtils import TopologyExplorer
from OCC.Core.STEPControl import STEPControl_Reader
from OCC.Core.IFSelect import IFSelect_RetDone, IFSelect_ItemsByEntity
from OCC.Extend.DataExchange import read_step_file_with_names_colors

#app.config["MODEL_UPLOADS"] = "/home/todd_kuehnl/atdapi/app/uploads"
app.config["MODEL_UPLOADS"] = "C:/Users/todd/atd/atdapi/app/uploads"
app.config["ALLOWED_IMAGE_EXTENSIONS"] = ["STEP"]

def allowed_image(filename):

    if not "." in filename:
        return False

    ext = filename.rsplit(".", 1)[1]

    if ext.upper() in app.config["ALLOWED_IMAGE_EXTENSIONS"]:
        return True
    else:
        return False

@app.route("/")
def index():
    return render_template("public/index.html")

@app.route("/admin/dashboard")
def admin_dashboard():
    return render_template("admin/dashboard.html")

@app.route("/about")
def about():
    return render_template("public/about.html")

def send_models(modelname):
    outputdir = os.path.join(app.config["MODEL_UPLOADS"], modelname )
    files = os.listdir(outputdir)
    return files

@app.route("/modelview/<modelname>")
def modelview(modelname):
    return render_template("public/modelview.html", modelname=modelname, models=send_models(modelname))

@app.route("/modelview/<modelname>/<model>")
def singlemodelview(modelname,model):
    return render_template("public/singleviewer.html", modelname=modelname, model=model, models=send_models(modelname))

@app.route("/uploads/<path:path>")
def send_uploads(path):
    return send_from_directory('uploads', path)

def zipFilesInDir(dirName, zipFileName, filter):
    with ZipFile(zipFileName, 'w') as zipObj:
       # Iterate over all the files in directory
       for folderName, subfolders, filenames in os.walk(dirName):
           for filename in filenames:
               if filter(filename):
                   # create complete filepath of file in directory
                   filePath = os.path.join(folderName, filename)
                   # Add file to zip
                   zipObj.write(filePath, basename(filePath))

@app.route("/upload-model", methods=["GET", "POST"])
def upload_model():

    if request.method == "POST":

        if request.files:

            model = request.files["model"]
            modelfile = os.path.join(app.config["MODEL_UPLOADS"], model.filename)
            model.save(modelfile)
            filename, file_extension = os.path.splitext(model.filename)
            #make output directory
            outputdir = os.path.join(app.config["MODEL_UPLOADS"], filename )
            if not os.path.exists(outputdir):
                os.makedirs(outputdir)

            big_shp = read_step_file(modelfile)
            #shapes_labels_colors = read_step_file_with_names_colors(modelfile)
            #shapes = []
            all_subshapes = TopologyExplorer(big_shp).solids()
            i = 0
            for single_shape in all_subshapes:
                tess = ShapeTesselator(single_shape)
                tess.Compute(compute_edges=False, mesh_quality=0.5)
                jsonfile = filename + "_" + str(i) + ".json"
                with open(os.path.join(outputdir, jsonfile), "w") as text_file:
                    json_shape = tess.ExportShapeToThreejsJSONString(filename + "_" + str(i))
                    json_shape = json_shape.replace("data\\", "data/")
                    json_shape = json_shape.replace("\\step_postprocessed\\", "/step_postprocessed/")
                    text_file.write(json_shape)
                i+=1
            #createZipFile
            zipfileName = os.path.join(outputdir, filename + ".zip")
            zipFilesInDir(outputdir, zipfileName, lambda name : 'json' in name)
            #Export each subshape
            #for shpt_lbl_color in shapes_labels_colors:
            #    label, c = shapes_labels_colors[shpt_lbl_color]
            #    tess = ShapeTesselator(shpt_lbl_color)
            #    tess.Compute(compute_edges=False, mesh_quality=0.5)
            #    jsonfile = label + ".json"
            #    with open(os.path.join(outputdir, jsonfile), "w") as text_file:
            #        json_shape = tess.ExportShapeToThreejsJSONString(label)
            #        json_shape = json_shape.replace("data\\", "data/")
            #        json_shape = json_shape.replace("\\step_postprocessed\\", "/step_postprocessed/")
            #        text_file.write(json_shape)
            return redirect(url_for('modelview', modelname = filename))

    return render_template("public/upload.html")
