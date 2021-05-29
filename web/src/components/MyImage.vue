<template>
  <div>
    <v-card>
<!--      <v-card-actions>-->
<!--        <v-spacer></v-spacer>-->
<!--      </v-card-actions>-->


<!--      <div class="d-flex justify-center">-->
<!--        <canvas id="canvas" width="512" height="512"/>-->
<!--        &lt;!&ndash;        <img id="img" :src="imgSrc"/>&ndash;&gt;-->
<!--      </div>-->

<!--      <v-card-actions class="d-flex justify-center">-->
<!--        <v-btn color="warning" @click="save">-->
<!--          保存图片-->
<!--        </v-btn>-->
<!--      </v-card-actions>-->

    </v-card>
sadasdas
  </div>
</template>

<script>
import {fabric} from "fabric";

export default {
  name: "Image",
  data() {
    return {
      canvas: {},
      imgSrc: ""
    }
  },
  methods: {
    save() {

    }
  },
  mounted() {
    console.log("!!!!!!!")
    this.canvas = new fabric.Canvas("canvas", {});
  }
}
</script>

<style scoped>
img {
  display: none;
}


canvas {
  border: 1px solid black;
}
</style>