      if (Array.isArray(origin)) {
        const scaleDiff = newScale / previousScale - 1;
        const [top, left] = this.containerTopLeft;
        this.container.scrollLeft += (origin[0] - left) * scaleDiff;
        this.container.scrollTop += (origin[1] - top) * scaleDiff;
      }