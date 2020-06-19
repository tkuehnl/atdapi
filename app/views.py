from app import app

from flask import render_template
from flask import request, redirect, url_for, send_from_directory
import os

from OCC.Extend.DataExchange import read_step_file
from OCC.Core.Tesselator import ShapeTesselator

app.config["MODEL_UPLOADS"] = "/home/todd_kuehnl/atdapi/app/uploads"
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

@app.route("/modelview/<modelname>")
def modelview(modelname):
    print(modelname)
    
    return render_template("public/modelview.html", modelname=modelname)

@app.route("/uploads/<path:path>")
def send_uploads(path):
    return send_from_directory('uploads', path)

@app.route("/upload-model", methods=["GET", "POST"])
def upload_model():

    if request.method == "POST":

        if request.files:

            model = request.files["model"]
            modelfile = os.path.join(app.config["MODEL_UPLOADS"], model.filename)
            model.save(modelfile)
            filename, file_extension = os.path.splitext(model.filename)
            big_shp = read_step_file(modelfile)
            tess = ShapeTesselator(big_shp)
            tess.Compute(compute_edges=False, mesh_quality=1)
            jsonfile = filename + ".json"
            with open(os.path.join(app.config["MODEL_UPLOADS"], jsonfile), "w") as text_file:
                json_shape = tess.ExportShapeToThreejsJSONString(filename)
                json_shape = json_shape.replace("data\\", "data/")
                json_shape = json_shape.replace("\\step_postprocessed\\", "/step_postprocessed/")
                text_file.write(json_shape)
            return redirect(url_for('modelview', modelname = jsonfile))

    return render_template("public/upload.html")
