<template>
  <v-app app>
    <Bar/>
    <v-main>
      <v-container fluid>
        <router-view/>
      </v-container>
    </v-main>

  </v-app>
</template>

<script>
import Bar from "./components/Bar";

export default {
  name: 'App',
  components: {
    Bar,
  },
  data: () => ({
    //
  }),
};
</script>
