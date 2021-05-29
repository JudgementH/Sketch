<template>
  <div>
    <v-card>

      <v-card-actions>
        <v-btn-toggle color="primary accent-3" dense tile group>
          <v-btn @click="drawTypeChange('')">
            <v-icon>mdi-arrow-top-left</v-icon>
          </v-btn>
          <v-btn @click="drawTypeChange('pen')">
            <v-icon>mdi-pencil</v-icon>
          </v-btn>
          <v-btn @click="drawTypeChange('eraser')">
            <v-icon>mdi-eraser</v-icon>
          </v-btn>
        </v-btn-toggle>
        <v-spacer></v-spacer>
        <div>
          <v-btn icon @click="undo">
            <v-icon>mdi-undo</v-icon>
          </v-btn>
          <v-btn icon @click="clear">
            <v-icon>mdi-close</v-icon>
          </v-btn>
          <v-btn icon @click="uploadImg">
            <v-icon>mdi-file-upload</v-icon>
          </v-btn>
        </div>
      </v-card-actions>

      <div class="d-flex justify-center">
        <canvas id="canvas" width="512" height="512"/>
        <input type="file" @change="uploadImgChange" id="imgInput" accept="image/*"/>
        <img id="img" :src="imgSrc"/>
      </div>

      <v-card-actions class="d-flex justify-center">
        <v-btn color="warning" @click="sendImage">
          生成图片
        </v-btn>
<!--        <v-btn color="warning" @click="save">-->
<!--          保存图片-->
<!--        </v-btn>-->
      </v-card-actions>


    </v-card>
  </div>
</template>
<script>
import {fabric} from 'fabric'

export default {
  name: "Painter",
  data() {
    return {
      width: 256,
      height: 256,
      rect: [],
      canvas: {},
      showMenu: false,
      x: "",
      y: "",

      mouseFrom: {},
      mouseTo: {},
      drawType: null,  //当前绘制图像的种类
      canvasObjectIndex: 0,
      textbox: null,
      rectangleLabel: "warning",
      drawWidth: 2, //笔触宽度
      color: "#000000", //画笔颜色
      drawingObject: null, //当前绘制对象
      moveCount: 1, //绘制移动计数器
      doDrawing: false, // 绘制状态

      //polygon 相关参数
      polygonMode: false,
      pointArray: [],
      lineArray: [],
      activeShape: false,
      activeLine: "",
      line: {},

      delectKlass: {},
      imgFile: {},
      imgSrc: "",
      sendBase64: "",
    };
  },
  watch: {
    drawType() {
      this.canvas.selection = !this.drawType;
    },
    width() {
      this.canvas.setWidth(512)
    },
    height() {
      this.canvas.setHeight(512)
    },
  },
  methods: {
    // 把当前文件编码为base64，然后发送给后端
    sendImage() {
      var canvas = document.getElementById('canvas')
      var img = canvas.toDataURL('png')
      this.sendBase64 = img
      this.$emit('sendImage', this.sendBase64)
    },
    // 保存当前画布为png图片
    save() {
      var canvas = document.getElementById('canvas')
      var imgData = canvas.toDataURL('png');
      imgData = imgData.replace('image/png', 'image/octet-stream');

      // 下载后的问题名，可自由指定
      var filename = 'drawingboard_' + (new Date()).getTime() + '.' + 'png';
      this.saveFile(imgData, filename);
    },
    saveFile(data, filename) {
      var save_link = document.createElement('a');
      save_link.href = data;
      save_link.download = filename;

      var event = document.createEvent('MouseEvents');
      event.initMouseEvent('click', true, false, window, 0, 0, 0, 0, 0, false, false, false, false, 0, null);
      save_link.dispatchEvent(event);
    },
    uploadImg() {
      document.getElementById("imgInput").click();
    },
    undo() {
      this.canvas.remove(
          this.canvas.getObjects()[this.canvas.getObjects().length - 1]
      );
    },
    clear() {
      this.canvas.clear()
    },
    // 从已渲染的DOM元素加载图片至canvas
    loadExpImg() {
      var imgElement = document.getElementById("expImg"); //声明我们的图片
      var imgInstance = new fabric.Image(imgElement, {
        selectable: false
        // zIndex:-99,
      });
      this.canvas.add(imgInstance);
    },
    // 从文件加载图片至canvas
    uploadImgChange() {
      // 获取文件
      var eleImportInput = document.getElementById("imgInput");
      this.imgFile = eleImportInput.files[0];
      // var imgSrc = "", imgTitle = "";
      var imgTitle = ""
      // 从reader中获取选择文件的src
      if (/\.(jpe?g|png|gif)$/i.test(this.imgFile.name)) {
        var reader = new FileReader();
        var _this = this;
        reader.addEventListener(
            "load",
            function () {
              imgTitle = _this.imgFile.name;
              _this.imgSrc = this.result;
            },
            false
        );
        reader.readAsDataURL(this.imgFile);
      }
      console.log(imgTitle)
      var imgElement = document.getElementById("img"); //声明我们的图片

      imgElement.onload = () => {
        this.width = imgElement.width
        this.height = imgElement.height
        var imgInstance = new fabric.Image(imgElement, {
          zIndex: -1,
          selectable: false,
        });
        imgInstance.scaleToHeight(512)
        imgInstance.scaleToWidth(512)
        this.canvas.add(imgInstance);
      };
    },
    // 开始绘制时，指定绘画种类
    drawTypeChange(e) {
      this.drawType = e;
      this.canvas.skipTargetFind = !!e
      this.canvas.isDrawingMode = e === "pen";

    },
    onEraserDone(e) {
      // 橡皮擦模式：划线后，修改混合方式，并立刻渲染
      e.path.globalCompositeOperation = 'destination-out'
      this.canvas.renderAll()
    },
    // 鼠标按下时触发
    mousedown(e) {
      // 记录鼠标按下时的坐标
      var xy = e.pointer || this.transformMouse(e.e.offsetX, e.e.offsetY);
      this.mouseFrom.x = xy.x;
      this.mouseFrom.y = xy.y;
      this.doDrawing = true;
      if (this.drawType === "text") {
        this.drawing();
      }

      if (this.drawType === 'erase') {
        this.canvas.freeDrawingBrush.color = '#fff'
        this.canvas.on('path:created', this.onEraserDone)
      }

      if (this.textbox) {
        this.textbox.enterEditing();
        this.textbox.hiddenTextarea.focus();
      }


    },
    // 鼠标松开执行
    mouseup(e) {
      var xy = e.pointer || this.transformMouse(e.e.offsetX, e.e.offsetY);
      this.mouseTo.x = xy.x;
      this.mouseTo.y = xy.y;
      this.drawingObject = null;
      this.moveCount = 1;
      if (this.drawType != "polygon") {
        this.doDrawing = false;
      }
    },

    //鼠标移动过程中已经完成了绘制
    mousemove(e) {
      if (this.moveCount % 2 && !this.doDrawing) {
        //减少绘制频率
        return;
      }
      this.moveCount++;
      var xy = e.pointer || this.transformMouse(e.e.offsetX, e.e.offsetY);
      this.mouseTo.x = xy.x;
      this.mouseTo.y = xy.y;
      // 多边形与文字框特殊处理
      if (this.drawType != "text" || this.drawType != "polygon") {
        this.drawing(e);
      }
      if (this.drawType == "polygon") {
        if (this.activeLine && this.activeLine.class == "line") {
          var pointer = this.canvas.getPointer(e.e);
          this.activeLine.set({x2: pointer.x, y2: pointer.y});

          var points = this.activeShape.get("points");
          points[this.pointArray.length] = {
            x: pointer.x,
            y: pointer.y,
            zIndex: 1
          };
          this.activeShape.set({
            points: points
          });
          this.canvas.renderAll();
        }
        this.canvas.renderAll();
      }
    },
    deleteObj() {
      this.canvas.getActiveObjects().map(item => {
        this.canvas.remove(item);
      });
    },
    transformMouse(mouseX, mouseY) {
      return {x: mouseX / 1, y: mouseY / 1};
    },
    // 绘制多边形开始，绘制多边形和其他图形不一样，需要单独处理
    drawPolygon() {
      this.drawType = "polygon";
      this.polygonMode = true;
      //这里画的多边形，由顶点与线组成
      this.pointArray = new Array();  // 顶点集合
      this.lineArray = new Array();  //线集合
      this.canvas.isDrawingMode = false;
    },
    addPoint(e) {
      var random = Math.floor(Math.random() * 10000);
      var id = new Date().getTime() + random;
      var circle = new fabric.Circle({
        radius: 5,
        fill: "#ffffff",
        stroke: "#333333",
        strokeWidth: 0.5,
        left: (e.pointer.x || e.e.layerX) / this.canvas.getZoom(),
        top: (e.pointer.y || e.e.layerY) / this.canvas.getZoom(),
        selectable: false,
        hasBorders: false,
        hasControls: false,
        originX: "center",
        originY: "center",
        id: id,
        objectCaching: false
      });
      if (this.pointArray.length == 0) {
        circle.set({
          fill: "red"
        });
      }
      var points = [
        (e.pointer.x || e.e.layerX) / this.canvas.getZoom(),
        (e.pointer.y || e.e.layerY) / this.canvas.getZoom(),
        (e.pointer.x || e.e.layerX) / this.canvas.getZoom(),
        (e.pointer.y || e.e.layerY) / this.canvas.getZoom()
      ];

      this.line = new fabric.Line(points, {
        strokeWidth: 2,
        fill: "#999999",
        stroke: "#999999",
        class: "line",
        originX: "center",
        originY: "center",
        selectable: false,
        hasBorders: false,
        hasControls: false,
        evented: false,

        objectCaching: false
      });
      if (this.activeShape) {
        var pos = this.canvas.getPointer(e.e);
        points = this.activeShape.get("points");
        points.push({
          x: pos.x,
          y: pos.y
        });
        var polygon = new fabric.Polygon(points, {
          stroke: "#333333",
          strokeWidth: 1,
          fill: "#cccccc",
          opacity: 0.3,

          selectable: false,
          hasBorders: false,
          hasControls: false,
          evented: false,
          objectCaching: false
        });
        this.canvas.remove(this.activeShape);
        this.canvas.add(polygon);
        this.activeShape = polygon;
        this.canvas.renderAll();
      } else {
        var polyPoint = [
          {
            x: (e.pointer.x || e.e.layerX) / this.canvas.getZoom(),
            y: (e.pointer.y || e.e.layerY) / this.canvas.getZoom()
          }
        ];
        polygon = new fabric.Polygon(polyPoint, {
          stroke: "#333333",
          strokeWidth: 1,
          fill: "#cccccc",
          opacity: 0.3,

          selectable: false,
          hasBorders: false,
          hasControls: false,
          evented: false,
          objectCaching: false
        });
        this.activeShape = polygon;
        this.canvas.add(polygon);
      }
      this.activeLine = this.line;

      this.pointArray.push(circle);
      this.lineArray.push(this.line);
      this.canvas.add(this.line);
      this.canvas.add(circle);
    },
    generatePolygon() {
      var points = new Array();
      this.pointArray.map((point, index) => {
        console.log(index)
        points.push({
          x: point.left,
          y: point.top
        });
        this.canvas.remove(point);
      });
      this.lineArray.map((line, index) => {
        console.log(index)
        this.canvas.remove(line);
      });
      this.canvas.remove(this.activeShape).remove(this.activeLine);
      var polygon = new fabric.Polygon(points, {
        stroke: this.color,
        strokeWidth: this.drawWidth,
        fill: "rgba(255, 255, 255, 0)",
        opacity: 1,
        hasBorders: true,
        hasControls: false
      });
      this.canvas.add(polygon);

      this.activeLine = null;
      this.activeShape = null;
      this.polygonMode = false;
      this.doDrawing = false;
      this.drawType = null;
    },
    drawing() {
      if (this.drawingObject) {
        this.canvas.remove(this.drawingObject);
      }
      var canvasObject = null;
      var mouseFrom = this.mouseFrom,
          mouseTo = this.mouseTo;
      switch (this.drawType) {
        case "arrow": //箭头
          var x1 = mouseFrom.x,
              x2 = mouseTo.x,
              y1 = mouseFrom.y,
              y2 = mouseTo.y;
          var w = x2 - x1,
              h = y2 - y1,
              sh = Math.cos(Math.PI / 4) * 16;
          var sin = h / Math.sqrt(Math.pow(w, 2) + Math.pow(h, 2));
          var cos = w / Math.sqrt(Math.pow(w, 2) + Math.pow(h, 2));
          var w1 = (16 * sin) / 4,
              h1 = (16 * cos) / 4,
              centerx = sh * cos,
              centery = sh * sin;
          /**
           * centerx,centery 表示起始点，终点连线与箭头尖端等边三角形交点相对x，y
           * w1 ，h1用于确定四个点
           */

          var path = " M " + x1 + " " + y1;
          path += " L " + (x2 - centerx + w1) + " " + (y2 - centery - h1);
          path +=
              " L " + (x2 - centerx + w1 * 2) + " " + (y2 - centery - h1 * 2);
          path += " L " + x2 + " " + y2;
          path +=
              " L " + (x2 - centerx - w1 * 2) + " " + (y2 - centery + h1 * 2);
          path += " L " + (x2 - centerx - w1) + " " + (y2 - centery + h1);
          path += " Z";
          canvasObject = new fabric.Path(path, {
            stroke: this.color,
            fill: this.color,
            strokeWidth: this.drawWidth
          });
          break;
        default:
          break;
      }

      if (canvasObject) {
        // canvasObject.index = getCanvasObjectIndex();\
        this.canvas.add(canvasObject); //.setActiveObject(canvasObject)
        this.drawingObject = canvasObject;
      }
    }
  },
  mounted() {
    this.canvas = new fabric.Canvas("canvas", {
      // skipTargetFind: false, //当为真时，跳过目标检测。目标检测将返回始终未定义。点击选择将无效
      // selectable: false,  //为false时，不能选择对象进行修改
      // selection: false   // 是否可以多个对象为一组
    });
    this.canvas.selectionColor = "rgba(0,0,0,0.05)";
    this.canvas.on("mouse:down", this.mousedown);
    this.canvas.on("mouse:move", this.mousemove);
    this.canvas.on("mouse:up", this.mouseup);

    document.onkeydown = e => {
      // 键盘 delect删除所选元素
      if (e.keyCode == 46) {
        this.deleteObj();
      }
      // ctrl+z 删除最近添加的元素
      if (e.keyCode == 90 && e.ctrlKey) {
        this.canvas.remove(
            this.canvas.getObjects()[this.canvas.getObjects().length - 1]
        );
      }
    };
    // var originalRender = fabric.Textbox.prototype._render;
    // fabric.Textbox.prototype._render = function(ctx) {
    //   originalRender.call(this, ctx);
    //   //Don't draw border if it is active(selected/ editing mode)
    //   if (this.active) return;
    //   if(this.showTextBoxBorder){
    //     var w = this.width,
    //       h = this.height,
    //       x = -this.width / 2,
    //       y = -this.height / 2;
    //     ctx.beginPath();
    //     ctx.moveTo(x, y);
    //     ctx.lineTo(x + w, y);
    //     ctx.lineTo(x + w, y + h);
    //     ctx.lineTo(x, y + h);
    //     ctx.lineTo(x, y);
    //     ctx.closePath();
    //     var stroke = ctx.strokeStyle;
    //     ctx.strokeStyle = this.textboxBorderColor;
    //     ctx.stroke();
    //     ctx.strokeStyle = stroke;
    //   }
    // }
    // fabric.Textbox.prototype.cacheProperties = fabric.Textbox.prototype.cacheProperties.concat('active');
  }
};
</script>

<style lang="scss" scoped>
.el-container {
  flex-direction: column;
}

img,
input {
  display: none;
}


canvas {
  border: 1px solid black;
}

.draw-btn-group {
  // width: 1270px;
  margin-top: 10px;
  display: flex;
  align-items: center;
  justify-content: flex-start;

  & > div {
    background: #fafafa;
    cursor: pointer;

    &:hover {
      background: #eee;
    }

    i {
      display: flex;
      background-repeat: no-repeat;
      background-size: 80%;
      background-position: 50% 50%;
      height: 30px;
      width: 30px;
    }

  }

  .active {
    background: #f30f0f;
  }
}
</style>
