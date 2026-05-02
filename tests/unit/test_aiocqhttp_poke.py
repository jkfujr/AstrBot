from unittest.mock import AsyncMock

import pytest

import astrbot.core.message.components as Comp
from astrbot.core.message.message_event_result import MessageChain
from astrbot.core.pipeline.respond.stage import RespondStage
from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import (
    AiocqhttpMessageEvent,
)


def test_poke_to_dict_matches_onebot_v11_segment_format():
    poke = Comp.Poke(type="126", id=2003)
    assert poke.toDict() == {
        "type": "poke",
        "data": {"type": "126", "id": "2003"},
    }


@pytest.mark.asyncio
async def test_respond_stage_treats_poke_with_target_as_non_empty():
    stage = RespondStage()
    chain = [Comp.Poke(type="126", id=2003)]
    assert await stage._is_empty_message_chain(chain) is False


@pytest.mark.asyncio
async def test_aiocqhttp_parse_json_outputs_standard_poke_data():
    chain = MessageChain([Comp.Poke(type="126", id=2003)])
    data = await AiocqhttpMessageEvent._parse_onebot_json(chain)
    assert data == [{"type": "poke", "data": {"type": "126", "id": "2003"}}]


@pytest.mark.asyncio
async def test_aiocqhttp_send_message_dispatches_onebot_v11_poke_payload():
    bot = AsyncMock()
    chain = MessageChain([Comp.Poke(type="126", id=2003)])

    await AiocqhttpMessageEvent.send_message(
        bot=bot,
        message_chain=chain,
        event=None,
        is_group=True,
        session_id="123456",
    )

    bot.send_group_msg.assert_awaited_once_with(
        group_id=123456,
        message=[{"type": "poke", "data": {"type": "126", "id": "2003"}}],
    )


def test_message_chain_use_remote_image_url_is_preserved_by_derive():
    chain = MessageChain([Comp.Image.fromURL("https://example.com/a.jpg")])

    assert chain.use_remote_image_url(True) is chain

    derived = chain.derive([Comp.Plain("ok")])
    assert derived.use_remote_image_url_ is True


@pytest.mark.asyncio
async def test_aiocqhttp_remote_image_url_uses_base64_by_default(monkeypatch):
    image = Comp.Image.fromURL("https://example.com/a.jpg")
    convert_to_base64 = AsyncMock(return_value="abc")
    monkeypatch.setattr(Comp.Image, "convert_to_base64", convert_to_base64)

    data = await AiocqhttpMessageEvent._parse_onebot_json(MessageChain([image]))

    convert_to_base64.assert_awaited_once()
    assert data == [{"type": "image", "data": {"file": "base64://abc"}}]


@pytest.mark.asyncio
async def test_aiocqhttp_remote_image_url_can_be_sent_directly(monkeypatch):
    image = Comp.Image.fromURL("https://example.com/a.jpg")
    convert_to_base64 = AsyncMock()
    monkeypatch.setattr(Comp.Image, "convert_to_base64", convert_to_base64)
    chain = MessageChain([image]).use_remote_image_url(True)

    data = await AiocqhttpMessageEvent._parse_onebot_json(chain)

    convert_to_base64.assert_not_awaited()
    assert data == [{"type": "image", "data": {"file": "https://example.com/a.jpg"}}]


@pytest.mark.asyncio
async def test_aiocqhttp_base64_image_ignores_remote_image_url(monkeypatch):
    image = Comp.Image.fromBase64("abc")
    convert_to_base64 = AsyncMock(return_value="abc")
    monkeypatch.setattr(Comp.Image, "convert_to_base64", convert_to_base64)
    chain = MessageChain([image]).use_remote_image_url(True)

    data = await AiocqhttpMessageEvent._parse_onebot_json(chain)

    convert_to_base64.assert_awaited_once()
    assert data == [{"type": "image", "data": {"file": "base64://abc"}}]


@pytest.mark.asyncio
async def test_aiocqhttp_file_image_ignores_remote_image_url(monkeypatch):
    image = Comp.Image.fromFileSystem("a.jpg")
    convert_to_base64 = AsyncMock(return_value="abc")
    monkeypatch.setattr(Comp.Image, "convert_to_base64", convert_to_base64)
    chain = MessageChain([image]).use_remote_image_url(True)

    data = await AiocqhttpMessageEvent._parse_onebot_json(chain)

    convert_to_base64.assert_awaited_once()
    assert data == [{"type": "image", "data": {"file": "base64://abc"}}]


@pytest.mark.asyncio
async def test_aiocqhttp_record_ignores_remote_image_url(monkeypatch):
    record = Comp.Record.fromURL("https://example.com/a.wav")
    convert_to_base64 = AsyncMock(return_value="abc")
    monkeypatch.setattr(Comp.Record, "convert_to_base64", convert_to_base64)
    chain = MessageChain([record]).use_remote_image_url(True)

    data = await AiocqhttpMessageEvent._parse_onebot_json(chain)

    convert_to_base64.assert_awaited_once()
    assert data == [{"type": "record", "data": {"file": "base64://abc"}}]
