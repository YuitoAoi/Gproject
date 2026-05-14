<!-- 500页面 -->
<template>
  <LfpException
    :data="{
      title: '500',
      desc: '服务器错误',
      btnText: '返回首页',
      imgUrl
    }"
  />
</template>

<script setup lang="ts">
  import imgUrl from '@imgs/svg/500.svg'
  defineOptions({ name: 'Exception500' })
</script>
