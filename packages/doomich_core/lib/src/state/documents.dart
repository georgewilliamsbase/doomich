import 'dart:async';
import 'dart:typed_data';

import 'package:doomich_api/doomich_api.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'app.dart';

const processingStatuses = {'uploaded', 'scanning', 'parsing', 'indexing'};

class UploadProgress {
  const UploadProgress(this.filename, this.sent, this.total);
  final String filename;
  final int sent;
  final int total;
  double get fraction => total <= 0 ? 0 : sent / total;
}

/// Документы пользователя. Пока какой-то документ обрабатывается, список обновляется раз в 3 секунды.
class DocumentsController extends AsyncNotifier<List<DocumentOut>> {
  Timer? _poll;

  @override
  Future<List<DocumentOut>> build() async {
    ref.onDispose(() => _poll?.cancel());
    final docs = await ref.read(apiClientProvider).documents();
    _schedulePoll(docs);
    return docs;
  }

  void _schedulePoll(List<DocumentOut> docs) {
    _poll?.cancel();
    if (docs.any((d) => processingStatuses.contains(d.status))) {
      _poll = Timer(const Duration(seconds: 3), () async {
        try {
          final fresh = await ref.read(apiClientProvider).documents();
          state = AsyncData(fresh);
          _schedulePoll(fresh);
        } catch (_) {
          _schedulePoll(docs);
        }
      });
    }
  }

  Future<DocumentOut> upload({required String filename, String? path, Uint8List? bytes,
      void Function(UploadProgress p)? onProgress}) async {
    final doc = await ref.read(apiClientProvider).uploadDocument(
          filename: filename,
          path: path,
          bytes: bytes,
          onProgress: onProgress == null ? null : (s, t) => onProgress(UploadProgress(filename, s, t)),
        );
    final list = [doc, ...?state.value?.where((d) => d.id != doc.id)];
    state = AsyncData(list);
    _schedulePoll(list);
    return doc;
  }

  Future<void> remove(String id) async {
    await ref.read(apiClientProvider).deleteDocument(id);
    state = AsyncData([...?state.value?.where((d) => d.id != id)]);
  }
}

final documentsProvider = AsyncNotifierProvider<DocumentsController, List<DocumentOut>>(DocumentsController.new);

final chunkProvider = FutureProvider.autoDispose.family<ChunkOut, (String, String)>((ref, ids) {
  return ref.read(apiClientProvider).chunk(ids.$1, ids.$2);
});
