/// Ошибка API. [code] стабилен и используется для локализованного текста.
class ApiException implements Exception {
  ApiException(this.code, this.message, {this.status, this.details = const {}});

  final String code;
  final String message;
  final int? status;
  final Map<String, dynamic> details;

  bool get isNetwork => code == 'network';
  bool get isUnauthorized => status == 401;
  bool get isRateLimited => status == 429;

  @override
  String toString() => 'ApiException($code, $status): $message';

  static ApiException network([String message = 'нет соединения']) => ApiException('network', message);
}
