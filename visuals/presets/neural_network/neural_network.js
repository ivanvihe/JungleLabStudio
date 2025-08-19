class NeuralNetworkPreset {
    constructor(canvas) {
        this.canvas = canvas;
        this.audioData = { low: 0, mid: 0, high: 0 };
        this.startTime = Date.now();
        this.opacity = 1.0;
        this.init();
    }

    async init() {
        // Obtener contexto WebGPU
        if (!navigator.gpu) {
            throw new Error('WebGPU not supported');
        }

        this.adapter = await navigator.gpu.requestAdapter();
        this.device = await this.adapter.requestDevice();
        this.context = this.canvas.getContext('webgpu');
        
        const canvasFormat = navigator.gpu.getPreferredCanvasFormat();
        this.context.configure({
            device: this.device,
            format: canvasFormat,
        });

        // Crear shader
        const shaderCode = await this.loadShader();
        this.shaderModule = this.device.createShaderModule({
            code: shaderCode
        });

        // Crear buffer de uniformes
        this.uniformBuffer = this.device.createBuffer({
            size: 5 * 4, // 5 floats * 4 bytes
            usage: GPUBufferUsage.UNIFORM | GPUBufferUsage.COPY_DST,
        });

        // Crear bind group layout
        this.bindGroupLayout = this.device.createBindGroupLayout({
            entries: [{
                binding: 0,
                visibility: GPUShaderStage.FRAGMENT,
                buffer: { type: 'uniform' }
            }]
        });

        // Crear bind group
        this.bindGroup = this.device.createBindGroup({
            layout: this.bindGroupLayout,
            entries: [{
                binding: 0,
                resource: { buffer: this.uniformBuffer }
            }]
        });

        // Crear pipeline
        this.renderPipeline = this.device.createRenderPipeline({
            layout: this.device.createPipelineLayout({
                bindGroupLayouts: [this.bindGroupLayout]
            }),
            vertex: {
                module: this.shaderModule,
                entryPoint: 'vs_main',
            },
            fragment: {
                module: this.shaderModule,
                entryPoint: 'fs_main',
                targets: [{
                    format: canvasFormat,
                    blend: {
                        color: {
                            srcFactor: 'src-alpha',
                            dstFactor: 'one-minus-src-alpha',
                        },
                        alpha: {
                            srcFactor: 'src-alpha',
                            dstFactor: 'one-minus-src-alpha',
                        },
                    },
                }]
            },
            primitive: {
                topology: 'triangle-list',
            },
        });

        // Iniciar loop de renderizado
        this.render();
    }

    async loadShader() {
        // Aquí deberías cargar el contenido del archivo neural_network.wgsl
        // Por simplicidad, lo incluimos directamente
        return `
        struct Uniforms {
            time: f32,
            audio_low: f32,
            audio_mid: f32,
            audio_high: f32,
            opacity: f32,
        }

        @group(0) @binding(0) var<uniform> uniforms: Uniforms;

        // [Aquí va todo el código del shader que generé anteriormente]
        // ...resto del código del shader...
        `;
    }

    updateAudioData(audioData) {
        this.audioData = audioData;
    }

    setOpacity(opacity) {
        this.opacity = opacity;
    }

    render() {
        // Actualizar uniformes
        const currentTime = (Date.now() - this.startTime) / 1000.0;
        const uniformData = new Float32Array([
            currentTime,
            this.audioData.low || 0,
            this.audioData.mid || 0, 
            this.audioData.high || 0,
            this.opacity
        ]);

        this.device.queue.writeBuffer(this.uniformBuffer, 0, uniformData);

        // Renderizar
        const commandEncoder = this.device.createCommandEncoder();
        const textureView = this.context.getCurrentTexture().createView();

        const renderPassDescriptor = {
            colorAttachments: [{
                view: textureView,
                clearValue: { r: 0.0, g: 0.0, b: 0.0, a: 1.0 },
                loadOp: 'clear',
                storeOp: 'store',
            }]
        };

        const passEncoder = commandEncoder.beginRenderPass(renderPassDescriptor);
        passEncoder.setPipeline(this.renderPipeline);
        passEncoder.setBindGroup(0, this.bindGroup);
        passEncoder.draw(3, 1, 0, 0);
        passEncoder.end();

        this.device.queue.submit([commandEncoder.finish()]);

        // Continuar el loop
        requestAnimationFrame(() => this.render());
    }

    destroy() {
        // Cleanup recursos
        if (this.uniformBuffer) this.uniformBuffer.destroy();
    }
}

// Uso del preset
export function createNeuralNetworkPreset(canvas) {
    const preset = new NeuralNetworkPreset(canvas);
    
    // Escuchar datos de audio desde Tauri
    if (window.__TAURI__) {
        window.__TAURI__.event.listen('audio_data', (event) => {
            preset.updateAudioData(event.payload);
        });
    }
    
    return preset;
}