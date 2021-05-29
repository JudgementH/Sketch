<template>
  <div>
    <v-card :loading="loading_">
      <v-card-actions>
        <v-btn-toggle color="primary accent-3" dense tile group>
          <v-btn>
            <v-icon>mdi-arrow-top-left</v-icon>
          </v-btn>
        </v-btn-toggle>
      </v-card-actions>


      <div class="d-flex justify-center">
        <img v-if="fakeImgBs64_" id="img" :src="fakeImgBs64_" width="512" height="512"/>
        <canvas v-else id="canvas" width="512" height="512"/>
      </div>

      <v-card-actions class="d-flex justify-center">
        <v-btn color="warning" @click="save">
          保存图片
        </v-btn>
      </v-card-actions>

    </v-card>
  </div>
</template>

<script>
import {fabric} from "fabric";

export default {
  name: "MyImage",
  props: {
    loading_: {
      type: Boolean,
      required: true
    },
    fakeImgBs64_: {
      type: String,
      required: true
    }
  },
  data() {
    return {
      canvas: {},
      imgSrc: "",
    }
  },
  methods: {
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
  },
  mounted() {
    this.canvas = new fabric.Canvas("canvas", {});
    var imgElement = document.getElementById("img"); //声明我们的图片
    var imgInstance = new fabric.Image(imgElement, {
      zIndex: -1,
      selectable: false,
    });
    imgInstance.scaleToHeight(512)
    imgInstance.scaleToWidth(512)
    this.canvas.add(imgInstance);

  }
}
</script>

<style scoped>
img {
  border: 1px solid black;

}


canvas {
  border: 1px solid black;
}
</style>