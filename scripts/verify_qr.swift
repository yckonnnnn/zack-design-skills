// 用 macOS 原生 Vision 框架解码二维码。
//
// 为什么需要它：OpenCV 的 QRCodeDetector 对取景和缩放极度敏感——同一张图，
// 换个尺寸或重采样滤波器就时好时坏，毫无规律。它会给出**假阴性**，让你以为
// 生成的二维码坏了，其实好好的。
//
// Vision 是 iOS 相机扫码用的同一套引擎，判定结果可信。所以本仓库用它做
// 二维码的权威校验，OpenCV 只作为没有 Vision 时的退路。
//
// 用法（免编译，swift 可以直接解释执行）：
//     swift scripts/verify_qr.swift assets/wechat-qr.png
//
// 输出一行 JSON：
//     {"ok":true,"payloads":["https://weixin.qq.com/g/..."]}
//     {"ok":false,"payloads":[]}

import CoreImage
import Foundation
import Vision

let args = CommandLine.arguments
guard args.count > 1 else {
    FileHandle.standardError.write("用法: swift verify_qr.swift <图片路径>\n".data(using: .utf8)!)
    exit(2)
}

func emit(ok: Bool, payloads: [String], error: String? = nil) {
    let escaped = payloads
        .map { $0.replacingOccurrences(of: "\\", with: "\\\\")
                 .replacingOccurrences(of: "\"", with: "\\\"") }
        .map { "\"\($0)\"" }
        .joined(separator: ",")
    var json = "{\"ok\":\(ok),\"payloads\":[\(escaped)]"
    if let error {
        let e = error.replacingOccurrences(of: "\"", with: "\\\"")
        json += ",\"error\":\"\(e)\""
    }
    json += "}"
    print(json)
}

guard let image = CIImage(contentsOf: URL(fileURLWithPath: args[1])) else {
    emit(ok: false, payloads: [], error: "cannot load image")
    exit(0)
}

let request = VNDetectBarcodesRequest()
request.symbologies = [.qr]

let handler = VNImageRequestHandler(ciImage: image, options: [:])
do {
    try handler.perform([request])
    let payloads = (request.results ?? []).compactMap { $0.payloadStringValue }
    emit(ok: !payloads.isEmpty, payloads: payloads)
} catch {
    emit(ok: false, payloads: [], error: error.localizedDescription)
}
