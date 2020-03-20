import Element from "./Element";

class MultiSelect2 {
  constructor(element, config) {
    this._config = {...config};
    this._state = {
      opened: false,
    };
    this._icons = [];
    this.currentFocus = -1

    this._boundHandleClick = this._handleClick.bind(this);
    this._boundUnselectOption = this._unselectOption.bind(this);
    this._boundSortOptions = this._sortOptions.bind(this);
    this._boundArrows = this._arrows.bind(this);
    this._body = new Element(document.body);

    this._create(element);
    this._setValue();
  }

  _create(_element) {
    const element = typeof _element === "string" ? document.querySelector(_element) : _element;

    this._parent = new Element(element);
    this._select = new Element("div", {class: "multi-select__select"});
    this._selected_value = new Element("span", {class: "multi-select__label"});
    this._optionsDiv = new Element("div", {class: "multi-select__options"});

    this._select.append(this._selected_value.get());
    this._select.append(this._optionsDiv.get());
    this._parent.append(this._select.get());

    this._options = this._generateOptionsOfSelect();
    this._select.addEventListener("click", this._boundHandleClick);

    if (this._config.multiple) {
      this._select.addClass("multi-select__select--multiple");
    }
  }

  _generateOptionsOfSelect() {
    if (this._config.autocomplete) {
      this._autocomplete = new Element("input", {class: "multi-select__autocomplete", type: "text"});
      // Add Listeners to input field of autocomplete
      this._autocomplete.addEventListener("input", this._boundSortOptions);
      this._autocomplete.addEventListener("keydown", this._boundArrows);

      this._optionsDiv.append(this._autocomplete.get());
    }

    return this._config.options.map(_option => {
      const option = new Element("div", {
        class: "multi-select__option",
        value: _option.value,
        textContent: _option.label,
        disabled: _option.disabled,
        info: _option.info,
        action: _option.action
      });

      this._optionsDiv.append(option.get());

      return option;
    });
  }

  _handleClick(event) {
    // reset dropdown
    this._firstActive();
    event.stopPropagation();
    this._closeAllLists();

    if (event.target.className === "multi-select__autocomplete") {
      return;
    }

    if (this._state.opened) {
      const option = this._options.find(_option => _option.get() === event.target);

      if (option) {
        this._setValue(option.get().getAttribute("data-value"), true);
      }

      this._select.removeClass("multi-select__select--opened");
      this._body.removeEventListener("click", this._boundHandleClick);
      this._select.addEventListener("click", this._boundHandleClick);

      this._state.opened = false;
      return;
    }

    //Check for fontawsome icon, incase of pro fontawsome it will check svg otherwise it will check i tag or class like fa fas-something
    if ('fa ' + event.target.parentElement.classList[1] === this._config.icon) {
      this._unselectOption(event.target.parentElement.getAttribute('data-value'));
      return;
    }else if (event.target.tagName === 'I') {
      this._unselectOption(event.target.getAttribute('data-value'));
      return;
    }else if (event.target.tagName === 'svg') {
      this._unselectOption(event.target.getAttribute('data-value'));
      return;
    }

    this._select.addClass("multi-select__select--opened");
    this._body.addEventListener("click", this._boundHandleClick);
    this._select.removeEventListener("click", this._boundHandleClick);

    this._state.opened = true;

    if (this._autocomplete) {
      this._autocomplete.focus();
    }
  }

  _setValue(value, manual, unselected) {
    if (value && !unselected) {
      this._config.value = this._config.multiple ? this._config.value.concat(value) : value;
    }
    if (value && unselected) {
      this._config.value = value;
    }

    this._options.forEach(_option => {
      _option.removeClass("multi-select__option--selected");
    });

    if (this._config.multiple) {
      const options = this._config.value.map(_value => {
        const option = this._config.options.find(_option => _option.value === _value);
        const optionNode = this._options.find(
          _option => _option.get().getAttribute("data-value") === option.value.toString()
        );

        optionNode.addClass("multi-select__option--selected");

        return option;
      });

      this._selectOptions(options, manual);

      return;
    }

    if (!this._config.options.length) {
      return;
    }

    const option = this._config.value ?
      this._config.options.find(_option => _option.value.toString() === this._config.value) : '';

    if (option !== '') {
      const optionNode = this._options.find(
        _option => _option.get().getAttribute("data-value") === option.value.toString()
      );

      optionNode.addClass("multi-select__option--selected");
      this._selectOption(option, manual);
    }
  }

  _selectOption(option, manual) {
    this._selectedOption = option;

    this._selected_value.setText(option.label);

    if (this._config.onChange && manual) {
      this._config.onChange(option.value);
    }
  }

  _selectOptions(options, manual) {
    this._selected_value.setText("");

    this._icons = options.map(_option => {
      const selectedLabel = new Element("span", {
        class: "multi-select__selected-label",
        textContent: _option.label,
      });
      const icon = new Element("i", {
        class: this._config.icon,
        value: _option.value,
      });

      selectedLabel.append(icon.get());
      this._selected_value.append(selectedLabel.get());

      return icon.get();
    });

    if (manual) {
      // eslint-disable-next-line no-magic-numbers
      this._optionsDiv.setTop(Number(this._select.getHeight().split("px")[0]) + 5);
    }

    if (this._config.onChange && manual) {
      this._config.onChange(this._config.value);
    }
  }

  _unselectOption(event) {
    const newValue = [...this._config.value];
    let index;
    if (!event.target) {
      index = newValue.indexOf(event);
    } else {
      index = newValue.indexOf(event.target.getAttribute("data-value"));
    }

    // eslint-disable-next-line no-magic-numbers
    if (index !== -1) {
      newValue.splice(index, 1);
    }

    this._setValue(newValue, true, true);
  }

  _sortOptions(event) {
    this._options.forEach(_option => {
      if (!_option.get().textContent.toLowerCase().includes(event.target.value.toLowerCase())) {
        _option.addClass("multi-select__option--hidden");
        return;
      }
      _option.removeClass("multi-select__option--hidden");
    });
    this._firstActive();
  }

  // return visible options
  _visibleOptions() {
    return this._optionsDiv.get().querySelectorAll('div.multi-select__option:not(.multi-select__option--hidden)');
  }

  // return visible options + unselected options
  _unselectedOptions() {
    return this._optionsDiv.get().querySelectorAll('div.multi-select__option:not(.multi-select__option--selected):not(.multi-select__option--hidden)');
  }

  // return selected options
  _selectedOptions() {
    return this._optionsDiv.get().querySelectorAll('.multi-select__option--selected');
  }

  // Arrow up, down, enter and tab button functionality
  _arrows(t) {
    let x = this._visibleOptions();
    if (t.keyCode == 40) {
      // this.currentFocus++;
      this._nextUnselected(x);
      this._addActive(x);
    } else if (t.keyCode == 38) {
      // this.currentFocus--;
      this._previousUnselected(x);
      this._addActive(x);
    } else if (t.keyCode == 13 || t.keyCode == 9) {
      t.preventDefault();
      if (this.currentFocus > -1) {
        /*and simulate a click on the "active" item:*/
        if (x) x[this.currentFocus].click();
        this._removeActive(x);
      }
    }
  }

  // Add active color on active item in dropdown
  _addActive(x) {
    /*a function to classify an item as "active":*/
    if (!x) return false;
    /*start by removing the "active" class on all items:*/
    this._removeActive(x);
    // checks if list ends or starts and set current fouces accordingly
    this._listEndingCheck(x);

    x[this.currentFocus].classList.add("multi-select__option-active");
    x[this.currentFocus].scrollIntoView();
  }

  /*a function to remove the "active" class from all autocomplete items:*/
  _removeActive(x) {
    for (var i = 0; i < x.length; i++) {
      x[i].classList.remove("multi-select__option-active");
    }
  }

  // select the next unselected value from dropdown
  _nextUnselected(x) {
    this.currentFocus++;
    while (x[this.currentFocus] && x[this.currentFocus].classList.contains('multi-select__option--selected')) {
      this.currentFocus++;
    }
  }

  // get the previous unselected element from dropdown
  _previousUnselected(x) {
    this.currentFocus--;
    while (x[this.currentFocus] && x[this.currentFocus].classList.contains('multi-select__option--selected')) {
      this.currentFocus--;
    }
  }

  // check if list ends or the start of list
  _listEndingCheck(x) {
    if (this.currentFocus >= x.length) {
      this.currentFocus = -1;
      this._nextUnselected(x);
    }

    if (this.currentFocus < 0) {
      this.currentFocus = (x.length);
      this._previousUnselected(x);
    }
  }

  // get the first active element from dropdown
  _firstActive() {
    this.currentFocus = -1;
    this._removeActive(this._visibleOptions());
    if (this._config.autocomplete) {
      if (this._unselectedOptions().length > 0) {
        this._nextUnselected(this._visibleOptions());
        this._visibleOptions()[this.currentFocus].classList.add("multi-select__option-active");
      }
    }
  }

  // On opening of select close all other selects
  _closeAllLists() {
    let elements = document.getElementsByClassName('multi-select__select');
    for (let i = 0; i < elements.length; i++) {
      if (elements[i] !== this._select.get()) {
        if (elements[i].classList.contains('multi-select__select--opened')) {
          elements[i].classList.remove('multi-select__select--opened');
        }
      }
    }
  }
}

export default MultiSelect2;
