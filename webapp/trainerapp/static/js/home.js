Vue.component('upload-files', {
  props: ['id', 'title'],
  data: function() {
    return {
      successModal: false,
      failModal: false,
    }
  },
  methods: {
    fileUpload: function(id) {
      let fileList = this.$refs.files.files;
      let formData = new FormData();
      for (let i = 0; i < fileList.length; i++) {
        formData.append(`file${i}`, fileList[i]);
      }

      this.$http.post(`/upload/${this.id}`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
          'X-CSRFToken': Cookies.get('csrftoken')
        }
      }).then((resp) => {
        if (resp.status === 200)
          this.successModal = true;
        else {
          console.log(err);
          this.failModal = true;
        }
      }).catch((err) => {
        this.failModal = true;
      });
    }
  },
  template: `
  <div class="file-upload ">
    <span>
    <button class="btn btn-primary" @click="$refs.files.click()"><i class="fas fa-upload"></i></button>
    <input style="display: none;" ref="files" multiple type="file" 
        accept=".json,.txt,.text,text" v-on:change="fileUpload(id)"/>
    </span>
    <modal v-if="successModal">
        <h3 slot="header" class="text-success">Save Successful</h3>
        <div slot="body"></div>
        <div slot="footer">
          <button class="btn btn-primary" @click="trainUseCase">Label Items</button>
        </div>
    </modal>
  
    <modal v-if="failModal">
      <h3 slot="header" class="text-danger">Save Failed</h3>
      <div slot="body">
        <p>Failed to upload training items for {{title}}.</p>
        <p>Please contact the dev team</p> 
      </div>
    </modal>
  </div>
  `
});

Vue.component('modal', {
  template: `
  <transition name="modal">
    <div class="modal-mask">
      <div class="modal-wrapper">
        <div class="modal-container">

          <div class="modal-header">
            <slot name="header">
              
            </slot>
          </div>

          <div class="modal-body">
            <slot name="body">
            </slot>
          </div>

          <div class="modal-footer">
            <slot name="footer">
            </slot>
          </div>
        </div>
      </div>
    </div>
  </transition>
`
});

let app = new Vue({
  el: '#app',
  data: {
    contexts: contexts(),
  },
});
