<template>
  <div>
    <v-row justify="center" style="padding-top: 50px;"></v-row>
    <v-row justify="center">
      <v-col cols="5">
        <Painter @sendImage="sendImage"/>
      </v-col>
      <v-col cols="5">
        <MyImage :loading_="loading" :fakeImgBs64_="fakeImgBs64"/>
      </v-col>
    </v-row>
  </div>
</template>

<script>
import Painter from "../components/Painter";
import MyImage from "../components/MyImage";

export default {
  name: "Main",
  components: {
    MyImage,
    Painter,
  },
  data() {
    return {
      loading: false,
      sendBase64: "",
      fakeImgBs64: "",
    }
  },
  methods: {
    sendImage(base64) {
      const that = this
      this.sendBase64 = base64
      this.loading = true
      let params = new FormData()
      params.append('imageData', this.sendBase64)
      this.axios.post('http://localhost:5000/generate', params).then((response) => {
        that.fakeImgBs64 = response.data.fake_image
        that.loading = false
      }).catch((response) => {
        console.log(response)
        that.loading = false
      })

    }
  }
}
</script>

<style scoped>

</style>