class Setting {
  constructor(name, hide_when_on, on) {
    this.name = name;
    this.hide_when_on = name;
    this.on = on;
  }

  turnOn() {
    this.on = true;
    this.hide_when_on.forEach((item, index) => {
      document
        .getElementsByClassName(item)
        .forEach((element, element_index) => {
          element.classList.remove('off');
        });
    });
  }

  turnOff() {
    this.on = false;
    this.hide_when_on.forEach((item, index) => {
      document
        .getElementsByClassName(item)
        .forEach((element, element_index) => {
          element.classList.add('off');
        });
    });
  }
}

document
  .querySelectorAll('.settings-radio')
  .forEach((element, element_index) => {
    element.addEventListener('change', event => {
      let class_to_hide = event.target.dataset.class_to_hide;
      let class_to_show = event.target.dataset.class_to_show;

      Array.from(document.getElementsByClassName(class_to_hide)).forEach(
        (element, element_index) => {
          element.classList.add('off');
        }
      );
      Array.from(document.getElementsByClassName(class_to_show)).forEach(
        (element, element_index) => {
          element.classList.remove('off');
        }
      );
    });
  });
