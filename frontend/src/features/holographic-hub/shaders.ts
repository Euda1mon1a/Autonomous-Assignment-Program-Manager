/**
 * Custom Shaders for Holographic Constraint Manifold
 *
 * These GLSL shaders provide high-performance rendering for:
 * - Constraint point particles with glow effects
 * - Constraint tension lines (connections between related constraints)
 * - Background grid/manifold surface
 * - Layer-specific visual effects (wavelength colors)
 *
 * Performance optimizations:
 * - Instanced rendering for thousands of points
 * - GPU-based animation calculations
 * - Level-of-detail based on camera distance
 */

// ============================================================================
// Constraint Point Vertex Shader
// ============================================================================

export const constraintPointVertexShader = /* glsl */ `
  // Attributes (per-instance)
  attribute vec3 instancePosition;
  attribute vec3 instanceColor;
  attribute float instanceSize;
  attribute float instanceOpacity;
  attribute float instanceGlow;
  attribute float instanceSeverity;
  attribute float instanceLayerIndex;

  // Uniforms
  uniform float time;
  uniform float pointScale;
  uniform float animationIntensity;
  uniform vec3 cameraPosition;
  uniform float layerVisibility[8]; // Visibility for each layer

  // Varyings (passed to fragment shader)
  varying vec3 vColor;
  varying float vOpacity;
  varying float vGlow;
  varying float vSeverity;
  varying float vDistanceToCamera;
  varying vec2 vUv;

  void main() {
    // Check layer visibility
    int layerIdx = int(instanceLayerIndex);
    float visibility = layerVisibility[layerIdx];

    // Animate position based on severity (violated constraints pulse)
    vec3 animatedPosition = instancePosition;
    if (instanceSeverity > 0.0) {
      float pulseSpeed = 2.0 + instanceSeverity * 3.0;
      float pulseAmount = sin(time * pulseSpeed) * 0.1 * instanceSeverity * animationIntensity;
      animatedPosition += normalize(instancePosition) * pulseAmount;
    }

    // Calculate distance to camera for LOD
    vec4 worldPosition = modelMatrix * vec4(animatedPosition, 1.0);
    vDistanceToCamera = distance(worldPosition.xyz, cameraPosition);

    // Adjust size based on distance (constant screen size)
    float distanceFactor = clamp(vDistanceToCamera / 10.0, 0.5, 2.0);
    float adjustedSize = instanceSize * pointScale / distanceFactor;

    // Apply visibility
    adjustedSize *= visibility;

    // Billboard calculation (face camera)
    vec3 cameraRight = vec3(viewMatrix[0][0], viewMatrix[1][0], viewMatrix[2][0]);
    vec3 cameraUp = vec3(viewMatrix[0][1], viewMatrix[1][1], viewMatrix[2][1]);

    vec3 vertexPosition = animatedPosition
      + cameraRight * position.x * adjustedSize
      + cameraUp * position.y * adjustedSize;

    gl_Position = projectionMatrix * viewMatrix * modelMatrix * vec4(vertexPosition, 1.0);

    // Pass to fragment
    vColor = instanceColor;
    vOpacity = instanceOpacity * visibility;
    vGlow = instanceGlow;
    vSeverity = instanceSeverity;
    vUv = uv;
  }
`;

// ============================================================================
// Constraint Point Fragment Shader
// ============================================================================

export const constraintPointFragmentShader = /* glsl */ `
  uniform float time;
  uniform bool showGlow;
  uniform float glowIntensity;

  varying vec3 vColor;
  varying float vOpacity;
  varying float vGlow;
  varying float vSeverity;
  varying float vDistanceToCamera;
  varying vec2 vUv;

  // Function to create soft circular point
  float circle(vec2 uv, float radius) {
    float dist = length(uv - 0.5);
    return smoothstep(radius, radius - 0.1, dist);
  }

  // Function to create glow effect
  float glow(vec2 uv, float radius, float intensity) {
    float dist = length(uv - 0.5);
    return intensity * (1.0 - smoothstep(0.0, radius * 2.0, dist));
  }

  void main() {
    vec2 uv = vUv;

    // Base circle
    float alpha = circle(uv, 0.4);

    // Add glow for high-severity constraints
    if (showGlow && vGlow > 0.0) {
      float glowAmount = glow(uv, 0.4, vGlow * glowIntensity);

      // Pulsing glow for critical constraints
      if (vSeverity > 0.8) {
        glowAmount *= 0.7 + 0.3 * sin(time * 4.0);
      }

      alpha = max(alpha, glowAmount);
    }

    // Apply opacity
    alpha *= vOpacity;

    // Discard fully transparent pixels
    if (alpha < 0.01) discard;

    // Color with severity-based tint
    vec3 finalColor = vColor;
    if (vSeverity > 0.5) {
      // Add red warning tint for violations
      float warningMix = (vSeverity - 0.5) * 2.0;
      finalColor = mix(vColor, vec3(1.0, 0.3, 0.2), warningMix * 0.5);
    }

    // Add distance-based fog
    float fogFactor = smoothstep(20.0, 50.0, vDistanceToCamera);
    finalColor = mix(finalColor, vec3(0.05, 0.05, 0.1), fogFactor * 0.5);

    gl_FragColor = vec4(finalColor, alpha);
  }
`;

// ============================================================================
// Tension Line Vertex Shader
// ============================================================================

export const tensionLineVertexShader = /* glsl */ `
  attribute vec3 startPosition;
  attribute vec3 endPosition;
  attribute vec3 lineColor;
  attribute float lineTension;
  attribute float lineProgress; // 0 = start, 1 = end

  uniform float time;
  uniform float tensionScale;

  varying vec3 vColor;
  varying float vTension;
  varying float vProgress;

  void main() {
    // Interpolate position along line
    vec3 pos = mix(startPosition, endPosition, lineProgress);

    // Add wave effect for high tension
    if (lineTension > 0.5) {
      float waveFreq = 10.0;
      float waveAmp = 0.05 * lineTension * tensionScale;

      vec3 lineDir = normalize(endPosition - startPosition);
      vec3 perpDir = normalize(cross(lineDir, vec3(0.0, 1.0, 0.0)));

      float wave = sin(lineProgress * waveFreq + time * 3.0) * waveAmp;
      pos += perpDir * wave;
    }

    gl_Position = projectionMatrix * modelViewMatrix * vec4(pos, 1.0);

    vColor = lineColor;
    vTension = lineTension;
    vProgress = lineProgress;
  }
`;

// ============================================================================
// Tension Line Fragment Shader
// ============================================================================

export const tensionLineFragmentShader = /* glsl */ `
  uniform float time;
  uniform float flowSpeed;

  varying vec3 vColor;
  varying float vTension;
  varying float vProgress;

  void main() {
    // Animated flow effect
    float flow = fract(vProgress - time * flowSpeed);
    float flowIntensity = smoothstep(0.0, 0.3, flow) * (1.0 - smoothstep(0.7, 1.0, flow));

    // Base opacity from tension
    float alpha = 0.3 + vTension * 0.5;
    alpha *= 0.5 + flowIntensity * 0.5;

    // Fade at endpoints
    alpha *= smoothstep(0.0, 0.1, vProgress) * (1.0 - smoothstep(0.9, 1.0, vProgress));

    vec3 finalColor = vColor * (0.7 + flowIntensity * 0.3);

    gl_FragColor = vec4(finalColor, alpha);
  }
`;

// ============================================================================
// Manifold Grid Vertex Shader
// ============================================================================

export const manifoldGridVertexShader = /* glsl */ `
  uniform float time;
  uniform float gridWaveIntensity;

  varying vec3 vWorldPosition;
  varying vec2 vUv;

  void main() {
    vec3 pos = position;

    // Add subtle wave animation to grid
    float wave = sin(pos.x * 0.5 + time * 0.5) * cos(pos.z * 0.5 + time * 0.3);
    pos.y += wave * gridWaveIntensity;

    vec4 worldPos = modelMatrix * vec4(pos, 1.0);
    vWorldPosition = worldPos.xyz;
    vUv = uv;

    gl_Position = projectionMatrix * viewMatrix * worldPos;
  }
`;

// ============================================================================
// Manifold Grid Fragment Shader
// ============================================================================

export const manifoldGridFragmentShader = /* glsl */ `
  uniform vec3 gridColor;
  uniform float gridOpacity;
  uniform float gridSize;
  uniform float lineWidth;

  varying vec3 vWorldPosition;
  varying vec2 vUv;

  float grid(vec2 pos, float size, float width) {
    vec2 grid = abs(fract(pos / size - 0.5) - 0.5) / fwidth(pos / size);
    float line = min(grid.x, grid.y);
    return 1.0 - min(line, 1.0);
  }

  void main() {
    // Primary grid
    float g1 = grid(vWorldPosition.xz, gridSize, lineWidth);

    // Secondary finer grid
    float g2 = grid(vWorldPosition.xz, gridSize * 0.2, lineWidth * 0.5) * 0.3;

    float alpha = max(g1, g2) * gridOpacity;

    // Fade with distance from origin
    float distFromOrigin = length(vWorldPosition.xz);
    alpha *= smoothstep(20.0, 5.0, distFromOrigin);

    if (alpha < 0.01) discard;

    gl_FragColor = vec4(gridColor, alpha);
  }
`;

// ============================================================================
// Layer Aura Shader (background glow for each spectral layer)
// ============================================================================

export const layerAuraVertexShader = /* glsl */ `
  varying vec3 vNormal;
  varying vec3 vWorldPosition;

  void main() {
    vNormal = normalize(normalMatrix * normal);
    vec4 worldPos = modelMatrix * vec4(position, 1.0);
    vWorldPosition = worldPos.xyz;
    gl_Position = projectionMatrix * viewMatrix * worldPos;
  }
`;

export const layerAuraFragmentShader = /* glsl */ `
  uniform vec3 auraColor;
  uniform float auraIntensity;
  uniform float time;
  uniform vec3 cameraPosition;

  varying vec3 vNormal;
  varying vec3 vWorldPosition;

  void main() {
    // Fresnel-like edge glow
    vec3 viewDir = normalize(cameraPosition - vWorldPosition);
    float fresnel = 1.0 - abs(dot(viewDir, vNormal));
    fresnel = pow(fresnel, 3.0);

    // Animated intensity
    float animatedIntensity = auraIntensity * (0.8 + 0.2 * sin(time * 0.5));

    float alpha = fresnel * animatedIntensity;

    gl_FragColor = vec4(auraColor, alpha);
  }
`;

// ============================================================================
// Shader Uniforms Interface
// ============================================================================

export interface ConstraintPointUniforms {
  time: { value: number };
  pointScale: { value: number };
  animationIntensity: { value: number };
  cameraPosition: { value: [number, number, number] };
  layerVisibility: { value: number[] };
  showGlow: { value: boolean };
  glowIntensity: { value: number };
}

export interface TensionLineUniforms {
  time: { value: number };
  tensionScale: { value: number };
  flowSpeed: { value: number };
}

export interface ManifoldGridUniforms {
  time: { value: number };
  gridWaveIntensity: { value: number };
  gridColor: { value: [number, number, number] };
  gridOpacity: { value: number };
  gridSize: { value: number };
  lineWidth: { value: number };
}

export interface LayerAuraUniforms {
  auraColor: { value: [number, number, number] };
  auraIntensity: { value: number };
  time: { value: number };
  cameraPosition: { value: [number, number, number] };
}

// ============================================================================
// Default Uniform Values
// ============================================================================

export function createConstraintPointUniforms(): ConstraintPointUniforms {
  return {
    time: { value: 0 },
    pointScale: { value: 1.0 },
    animationIntensity: { value: 1.0 },
    cameraPosition: { value: [0, 0, 10] },
    layerVisibility: { value: [1, 1, 1, 1, 1, 1, 1, 1] },
    showGlow: { value: true },
    glowIntensity: { value: 1.5 },
  };
}

export function createTensionLineUniforms(): TensionLineUniforms {
  return {
    time: { value: 0 },
    tensionScale: { value: 1.0 },
    flowSpeed: { value: 0.5 },
  };
}

export function createManifoldGridUniforms(): ManifoldGridUniforms {
  return {
    time: { value: 0 },
    gridWaveIntensity: { value: 0.1 },
    gridColor: { value: [0.2, 0.4, 0.6] },
    gridOpacity: { value: 0.3 },
    gridSize: { value: 2.0 },
    lineWidth: { value: 0.02 },
  };
}

export function createLayerAuraUniforms(): LayerAuraUniforms {
  return {
    auraColor: { value: [0.3, 0.5, 1.0] },
    auraIntensity: { value: 0.5 },
    time: { value: 0 },
    cameraPosition: { value: [0, 0, 10] },
  };
}
