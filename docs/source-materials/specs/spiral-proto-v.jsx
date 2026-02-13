<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Spiral Test</title>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.0/gsap.min.js"></script>
  <style>
    body {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      height: 100vh;
      margin: 0;
      background-color: #f5f1e9;
      font-family: Arial, sans-serif;
    }
    #spiral-svg {
      transform-origin: center;
      animation: rotate 12s linear infinite;
    }
    @keyframes rotate {
      to { transform: rotate(360deg); }
    }
    #spiral-path {
      stroke-dasharray: 1200;
      stroke-dashoffset: 1200;
      animation: draw 4s ease-out forwards;
    }
    @keyframes draw {
      to { stroke-dashoffset: 0; }
    }
    .controls {
      margin-top: 20px;
    }
    button {
      padding: 10px 20px;
      margin: 0 10px;
      font-size: 16px;
      cursor: pointer;
      border: 1px solid #333;
      border-radius: 5px;
      background-color: #fff;
    }
    button:hover {
      background-color: #f0f0f0;
    }
  </style>
</head>
<body>
  <svg id="spiral-svg" viewBox="0 0 400 400" width="400" height="400">
    <path
      id="spiral-path"
      d="M200,350
         C220,330 240,320 260,300
         C280,280 290,260 300,240
         C310,220 320,200 320,180
         C320,160 310,140 300,120
         C290,100 280,80 260,60
         C240,40 220,30 200,20
         C180,30 160,40 140,60
         C120,80 110,100 100,120
         C90,140 80,160 80,180
         C80,200 90,220 100,240
         C110,260 120,280 140,300
         C160,320 180,330 200,350
         Z"
      stroke="#333"
      fill="none"
      stroke-width="2"
    />
    <!-- Star markers approximated at key points along the spiral -->
    <circle cx="260" cy="300" r="2" fill="#333" />
    <circle cx="300" cy="240" r="2" fill="#333" />
    <circle cx="320" cy="180" r="2" fill="#333" />
    <circle cx="300" cy="120" r="2" fill="#333" />
    <circle cx="260" cy="60" r="2" fill="#333" />
    <circle cx="200" cy="20" r="2" fill="#333" />
    <circle cx="140" cy="60" r="2" fill="#333" />
    <circle cx="100" cy="120" r="2" fill="#333" />
    <circle cx="80" cy="180" r="2" fill="#333" />
    <circle cx="100" cy="240" r="2" fill="#333" />
    <circle cx="140" cy="300" r="2" fill="#333" />
  </svg>
  <div class="controls">
    <button onclick="resetAnimation()">Reset</button>
    <button onclick="triggerQuizProgress()">Simulate Quiz Progress</button>
  </div>

  <script>
    // Get the path length and initialize GSAP animation
    const path = document.querySelector('#spiral-path');
    const pathLength = path.getTotalLength();
    gsap.set(path, { strokeDasharray: pathLength, strokeDashoffset: pathLength });

    function resetAnimation() {
      gsap.to(path, { strokeDashoffset: pathLength, duration: 0.5, onComplete: () => {
        gsap.to(path, { strokeDashoffset: 0, duration: 4, ease: 'power2.out' });
      }});
    }

    function triggerQuizProgress() {
      const progress = Math.random() * 100; // Simulate random quiz progress (0-100%)
      const targetOffset = pathLength * (1 - progress / 100);
      gsap.to(path, { strokeDashoffset: targetOffset, duration: 1, ease: 'power2.out' });
      alert(`Simulated Quiz Progress: ${progress.toFixed(2)}%`);
    }

    // Initial draw animation
    gsap.to(path, { strokeDashoffset: 0, duration: 4, ease: 'power2.out' });
  </script>
</body>
</html>